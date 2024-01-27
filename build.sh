#!/bin/bash
set -e

DIRECTORY=$1
POETRY_SHORTHAND="poetry -C ${DIRECTORY}"
IMAGE_NAME=$(${POETRY_SHORTHAND} version | awk '{print $1}')
IMAGE_VERSION=$(${POETRY_SHORTHAND} version -s)

FULL_IMAGE_NAME=${REGISTRY_HOST}/${IMAGE_NAME}:${IMAGE_VERSION}

${POETRY_SHORTHAND} export -f requirements.txt -o "${DIRECTORY}/requirements.txt" --without-hashes

echo "Building image ${IMAGE_NAME}:${IMAGE_VERSION}"

docker build "${DIRECTORY}" -t "${FULL_IMAGE_NAME}"

rm "${DIRECTORY}/requirements.txt"

docker push "${FULL_IMAGE_NAME}"
