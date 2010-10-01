#!/bin/bash
TOOLS=`dirname $0`
VENV=$TOOLS/../.flomosa-venv
source $VENV/bin/activate && $@