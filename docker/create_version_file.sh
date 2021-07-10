#!/usr/bin/env sh

DIR=$(dirname "$0")
cd "${DIR}"

version_file="version.txt"

# Including the branch and version information plus details from last commit(s)
commit_amount=$(git rev-list HEAD --count)
branch=$(git branch --show-current)
last_commit_info=$(git log -1 --stat)
echo "Trezor-user-env information" > ${version_file}
echo "Version (commit amount): ${commit_amount}" >> ${version_file}
echo "Branch: ${branch}" >> ${version_file}
echo "" >> ${version_file}
echo "${last_commit_info}" >> ${version_file}
echo "********************************************************" >> ${version_file}
