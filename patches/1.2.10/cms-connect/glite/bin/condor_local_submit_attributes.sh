#! /bin/sh

if [ "x${required_os}" != "x" ]; then
  echo "+REQUIRED_OS = ${required_os}"
fi

if [ "x${desired_sites}" != "x" ]; then
  echo "+DESIRED_Sites = ${desired_sites}"
fi
