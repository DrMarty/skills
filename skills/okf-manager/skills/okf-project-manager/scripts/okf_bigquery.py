#!/usr/bin/env python3
"""Optional BigQuery concept discovery, metadata reads, and row sampling."""
from __future__ import annotations

import argparse
import json
import re
import sys

SHARD_SUFFIX_RE = re.compile(r"^(?P<prefix>.+?_)(?P<shard>\d{6,8})$")


def client_and_dataset(dataset: str, billing_project: str | None):
    try:
        from google.cloud import bigquery
    except Exception as exc:
        raise RuntimeError("BigQuery support is optional; install requirements-bigquery.txt into the OKF worker environment") from exc
    if "." not in dataset:
        raise ValueError("dataset must use project.dataset form")
    project, dataset_id = dataset.split(".", 1)
    client = bigquery.Client(project=billing_project or None)
    return client, bigquery.DatasetReference(project, dataset_id), project, dataset_id


def field_data(field) -> dict:
    result = {"name": field.name, "type": field.field_type, "mode": field.mode}
    if field.description:
        result["description"] = field.description
    if field.fields:
        result["fields"] = [field_data(child) for child in field.fields]
    return result


def list_concepts(dataset: str, billing_project: str | None) -> dict:
    client, dataset_ref, project, dataset_id = client_and_dataset(dataset, billing_project)
    concepts = [{
        "id": f"datasets/{dataset_id}",
        "type": "BigQuery Dataset",
        "resource": f"https://bigquery.googleapis.com/v2/projects/{project}/datasets/{dataset_id}",
    }]
    families: dict[str, list[str]] = {}
    singletons: list[str] = []
    for table in client.list_tables(dataset_ref):
        match = SHARD_SUFFIX_RE.match(table.table_id)
        if match:
            families.setdefault(match.group("prefix"), []).append(table.table_id)
        else:
            singletons.append(table.table_id)
    for prefix, shards in sorted(families.items()):
        ordered = sorted(shards)
        concepts.append({
            "id": f"tables/{prefix}",
            "type": "BigQuery Table",
            "resource": f"https://bigquery.googleapis.com/v2/projects/{project}/datasets/{dataset_id}/tables/{prefix}*",
            "hint": {"wildcard": True, "shard_count": len(ordered), "first_shard": ordered[0], "last_shard": ordered[-1]},
        })
    for table_id in sorted(singletons):
        concepts.append({
            "id": f"tables/{table_id}",
            "type": "BigQuery Table",
            "resource": f"https://bigquery.googleapis.com/v2/projects/{project}/datasets/{dataset_id}/tables/{table_id}",
            "hint": {"wildcard": False},
        })
    return {"dataset": dataset, "concept_count": len(concepts), "concepts": concepts}


def read_metadata(dataset: str, concept_id: str, billing_project: str | None) -> dict:
    client, dataset_ref, project, dataset_id = client_and_dataset(dataset, billing_project)
    kind, _, name = concept_id.partition("/")
    if kind == "datasets":
        item = client.get_dataset(dataset_ref)
        return {
            "dataset_project": project,
            "dataset_id": dataset_id,
            "friendly_name": item.friendly_name,
            "description": item.description,
            "location": item.location,
            "labels": dict(item.labels or {}),
            "created": item.created.isoformat() if item.created else None,
            "modified": item.modified.isoformat() if item.modified else None,
        }
    if kind != "tables" or not name:
        raise ValueError("concept_id must be datasets/<id> or tables/<id>")
    table_id = name
    if name.endswith("_"):
        shards = sorted(table.table_id for table in client.list_tables(dataset_ref) if table.table_id.startswith(name) and SHARD_SUFFIX_RE.match(table.table_id))
        if shards:
            table_id = shards[-1]
    table = client.get_table(dataset_ref.table(table_id))
    result = {
        "dataset_project": project,
        "dataset_id": dataset_id,
        "representative_table_id": table_id,
        "friendly_name": table.friendly_name,
        "description": table.description,
        "labels": dict(table.labels or {}),
        "num_rows": table.num_rows,
        "num_bytes": table.num_bytes,
        "created": table.created.isoformat() if table.created else None,
        "modified": table.modified.isoformat() if table.modified else None,
        "schema": [field_data(field) for field in table.schema or []],
    }
    if table.time_partitioning:
        result["time_partitioning"] = {
            "type": table.time_partitioning.type_,
            "field": table.time_partitioning.field,
            "expiration_ms": table.time_partitioning.expiration_ms,
        }
    if table.clustering_fields:
        result["clustering_fields"] = list(table.clustering_fields)
    return result


def sample_rows(dataset: str, concept_id: str, count: int, billing_project: str | None) -> dict:
    client, dataset_ref, project, dataset_id = client_and_dataset(dataset, billing_project)
    kind, _, table_id = concept_id.partition("/")
    if kind != "tables" or not table_id:
        raise ValueError("sampling requires a tables/<id> concept")
    table = client.get_table(dataset_ref.table(table_id))
    if getattr(table, "table_type", "TABLE") == "VIEW":
        rows = client.query(f"SELECT * FROM `{project}.{dataset_id}.{table_id}` LIMIT {count}").result()
    else:
        rows = client.list_rows(table, max_results=count)
    return {"rows": [{key: str(value) for key, value in dict(row.items()).items()} for row in rows], "note": ""}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Use optional BigQuery sources with OKF Manager")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--billing-project")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    command = sub.add_parser("read")
    command.add_argument("concept_id")
    command = sub.add_parser("sample")
    command.add_argument("concept_id")
    command.add_argument("--count", type=int, default=5)
    args = parser.parse_args(argv[1:])
    try:
        if args.command == "list":
            result = list_concepts(args.dataset, args.billing_project)
        elif args.command == "read":
            result = read_metadata(args.dataset, args.concept_id, args.billing_project)
        else:
            result = sample_rows(args.dataset, args.concept_id, args.count, args.billing_project)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "command": args.command, "error": str(exc)}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

