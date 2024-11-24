#!/usr/bin/env bash

settings::pre_release() {
  base::log_info "Updating version in pyproject.toml..."
  poetry version "${_arg__new_version}"
  git add pyproject.toml
}
