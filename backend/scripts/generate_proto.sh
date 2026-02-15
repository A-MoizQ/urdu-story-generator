#!/usr/bin/env bash
# generate_proto.sh — Compile .proto → Python stubs
#
# Usage:
#   cd backend/
#   bash scripts/generate_proto.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
PROTO_DIR="${BACKEND_DIR}/proto"

echo "▸ Generating Python gRPC stubs from ${PROTO_DIR}/story.proto"

python -m grpc_tools.protoc \
    -I "${PROTO_DIR}" \
    --python_out="${PROTO_DIR}" \
    --grpc_python_out="${PROTO_DIR}" \
    --pyi_out="${PROTO_DIR}" \
    "${PROTO_DIR}/story.proto"

# Fix relative import in generated grpc stub
# (grpc_tools generates `import story_pb2` but we need `from . import story_pb2`)
sed -i 's/^import story_pb2 as story__pb2$/from . import story_pb2 as story__pb2/' \
    "${PROTO_DIR}/story_pb2_grpc.py"

echo "✔ Proto stubs generated in ${PROTO_DIR}/"
