#!/bin/bash
# ABOUT
# CI shell script for Artisan builds to upload packaged files to Github
#
# Attribution
# This script was rewriten, simplified and adapted for Artisan Appveyor CI based on https://github.com/probonopd/uploadtool
# uploadtool.sh is published under the MIT license, Copyright (c) 2016 Simon Peter
# 
# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later versison. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.
#
# AUTHOR
# Dave Baxter, Rui Paulo, Marko Luther 2023
# Notes:
# only the file to upload is specified on the command line
# all necessary information comes from Appveyor environment variables

set +x # Do not leak information

# Exit immediately if there are no files or one of the files given as arguments is not there
if [ $# -eq 0 ]; then
    echo "No artifacts to use for release, giving up."
    exit 0
fi

for file in "$@"
do
    if [ ! -e "$file" ]
        then echo "$file is missing, giving up." >&2; exit 1
    fi
done

# Confirm existance of a tool
if command -v sha256sum >/dev/null 2>&1 ; then
    shatool="sha256sum"
elif command -v shasum >/dev/null 2>&1 ; then
    shatool="shasum -a 256" # macOS fallback
else
    echo "Neither sha256sum nor shasum is available, cannot check hashes"
fi

# Confirm running on Appveyor
if [ -z "$APPVEYOR" ]; then
    # We are not running on Appveyor CI
    echo "Not running on Appveyor CI"
    exit 0
fi

# Set the variables based on the Appveyor environment variables
APPVEYOR_REPO_NAME="$APPVEYOR_REPO_NAME"
APPVEYOR_REPO_TAG_NAME="$APPVEYOR_REPO_TAG_NAME"  #unused
APPVEYOR_BUILD_NUMBER="$APPVEYOR_BUILD_NUMBER"
APPVEYOR_BUILD_ID="$APPVEYOR_BUILD_ID"
APPVEYOR_REPO_BRANCH="$APPVEYOR_REPO_BRANCH"
APPVEYOR_REPO_COMMIT="$APPVEYOR_REPO_COMMIT"
APPVEYOR_JOB_ID="$APPVEYOR_JOB_ID"
APPVEYOR_BUILD_WEB_URL="${APPVEYOR_URL}/project/${APPVEYOR_ACCOUNT_NAME}/${APPVEYOR_PROJECT_SLUG}/build/job/${APPVEYOR_JOB_ID}"
RELEASE_NAME="continuous"
RELEASE_TITLE="Continuous build"
UPLOADTOOL_BODY="WARNING: pre-release builds may not work. Use at your own risk."
is_prerelease="true"
if [[ $APPVEYOR_REPO_COMMIT_MESSAGE =~ nodeploy ]] || [[ $APPVEYOR_REPO_COMMIT_MESSAGE_EXTENDED =~ nodeploy ]] ; then
    echo "Release uploading disabled, commit message contains 'nodeploy'"
    exit 0
fi

#this is in fact redundant since Appveyor does not execute deploy on public repostiries for pull requests
if [ ! -z "$APPVEYOR_PULL_REQUEST_NUMBER" ] ; then
    echo "Release uploading disabled for pull requests"
    exit 0
fi

# Confirm there is a repo commit value and that there is a valid Githuf token
if [ ! -z "$APPVEYOR_REPO_NAME" ] ; then
    # We are running on Appveyor CI
    echo "Running on Appveyor CI"
    echo "APPVEYOR_REPO_COMMIT: $APPVEYOR_REPO_COMMIT"
    if [ -z "$GITHUB_TOKEN" ] ; then
        echo "\$GITHUB_TOKEN missing, please set it in the Appveyor CI settings of this project"
        echo "You can get one from https://github.com/settings/tokens"
        exit 1
    fi
else
    # We are not running on Appveyor CI
    echo "Not running on Appveyor CI"
    exit 1
fi

# Setup URLs
tag_url="https://api.github.com/repos/$APPVEYOR_REPO_NAME/git/refs/tags/$RELEASE_NAME"
tag_infos=$(curl -XGET --header "Authorization: token ${GITHUB_TOKEN}" "${tag_url}")
echo "tag_infos: $tag_infos"
tag_sha=$(echo "$tag_infos" | grep '"sha":' | head -n 1 | cut -d '"' -f 4 | cut -d '{' -f 1)
echo "tag_sha: $tag_sha"

release_url="https://api.github.com/repos/$APPVEYOR_REPO_NAME/releases/tags/$RELEASE_NAME"
echo "Getting the release ID..."
echo "release_url: $release_url"
release_infos=$(curl -XGET --header "Authorization: token ${GITHUB_TOKEN}" "${release_url}")
echo "release_infos: $release_infos"
release_id=$(echo "$release_infos" | grep "\"id\":" | head -n 1 | tr -s " " | cut -f 3 -d" " | cut -f 1 -d ",")
echo "release ID: $release_id"
upload_url=$(echo "$release_infos" | grep '"upload_url":' | head -n 1 | cut -d '"' -f 4 | cut -d '{' -f 1)
echo "upload_url: $upload_url"
release_url=$(echo "$release_infos" | grep '"url":' | head -n 1 | cut -d '"' -f 4 | cut -d '{' -f 1)
echo "release_url: $release_url"
target_commit_sha=$(echo "$release_infos" | grep '"target_commitish":' | head -n 1 | cut -d '"' -f 4 | cut -d '{' -f 1)
echo "target_commit_sha: $target_commit_sha"

# Delete the Github release and tag when appropriate and setup the release
if [ "$APPVEYOR_REPO_COMMIT" != "$target_commit_sha" ] ; then
    echo "APPVEYOR_REPO_COMMIT != target_commit_sha, hence deleting $RELEASE_NAME..."

    if [ ! -z "$release_id" ]; then
        delete_url="https://api.github.com/repos/$APPVEYOR_REPO_NAME/releases/$release_id"
        echo "Delete the release..."
        echo "delete_url: $delete_url"
        curl -XDELETE \
            --header "Authorization: token ${GITHUB_TOKEN}" \
            "${delete_url}"
    fi

    if [ "$RELEASE_NAME" == "continuous" ] ; then
        # if this is a continuous build tag, then delete the old tag
        # in preparation for the new release
        echo "Delete the tag..."
        delete_url="https://api.github.com/repos/$APPVEYOR_REPO_NAME/git/refs/tags/$RELEASE_NAME"
        echo "delete_url: $delete_url"
        curl -XDELETE \
            --header "Authorization: token ${GITHUB_TOKEN}" \
            "${delete_url}"
    fi

    echo "Create release..."

    if [ -z "$APPVEYOR_REPO_BRANCH" ] ; then
        APPVEYOR_REPO_BRANCH="master"
    fi

    if [ ! -z "$APPVEYOR_JOB_ID" ] ; then
        if [ -z "${UPLOADTOOL_BODY+x}" ] ; then
            BODY="Appveyor CI build log: ${APPVEYOR_BUILD_WEB_URL}"
        else
            BODY="$UPLOADTOOL_BODY"
        fi
    else
        BODY="$UPLOADTOOL_BODY"
    fi

    release_infos=$(curl -H "Authorization: token ${GITHUB_TOKEN}" \
        --data '{"tag_name": "'"$RELEASE_NAME"'","target_commitish": "'"$APPVEYOR_REPO_COMMIT"'","name": "'"$RELEASE_TITLE"'","body": "'"$BODY"'","draft": false,"prerelease": '$is_prerelease'}' "https://api.github.com/repos/$APPVEYOR_REPO_NAME/releases")

    echo "$release_infos"

    unset upload_url
    upload_url=$(echo "$release_infos" | grep '"upload_url":' | head -n 1 | cut -d '"' -f 4 | cut -d '{' -f 1)
    echo "upload_url: $upload_url"

    unset release_url
    release_url=$(echo "$release_infos" | grep '"url":' | head -n 1 | cut -d '"' -f 4 | cut -d '{' -f 1)
    echo "release_url: $release_url"
fi

if [ -z "$release_url" ] ; then
    echo "Cannot figure out the release URL for $RELEASE_NAME"
    exit 1
fi

echo "Upload binaries to the release..."

# Need to URL encode the basename, so we have this function to do so
urlencode() {
    # urlencode <string>
    old_lc_collate=$LC_COLLATE
    LC_COLLATE=C
    local length="${#1}"
    for (( i = 0; i < length; i++ )); do
        local c="${1:$i:1}"
        case $c in
            [a-zA-Z0-9.~_-]) printf '%s' "$c" ;;
            *) printf '%%%02X' "'$c" ;;
        esac
    done
    LC_COLLATE=$old_lc_collate
}

# Upload each file
for FILE in "$@" ; do
    FULLNAME="${FILE}"
    BASENAME="$(basename "${FILE}")"
    curl -H "Authorization: token ${GITHUB_TOKEN}" \
         -H "Accept: application/vnd.github.manifold-preview" \
         -H "Content-Type: application/octet-stream" \
         --data-binary "@$FULLNAME" \
         "$upload_url?name=$(urlencode "$BASENAME")"
    echo ""
done

$shatool "$@"

if [ "$APPVEYOR_REPO_COMMIT" != "$tag_sha" ] ; then
    echo "Publish the release..."

    release_infos=$(curl -H "Authorization: token ${GITHUB_TOKEN}" \
        --data '{"draft": false}' "$release_url")

    echo "$release_infos"
fi
