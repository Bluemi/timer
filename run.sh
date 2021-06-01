#!/bin/bash

case "$1" in
	r)
		echo ""
		echo "timer.py pizza"
		python3 src/timer.py pizza

		echo ""
		echo "timer.py 0:02 essen"
		python3 src/timer.py 0:02 essen

		echo ""
		echo "timer.py --list"
		python3 src/timer.py --list;;
	d)
		python3 src/timerd.py;;
	*)
		echo "\$1 should be on of [r, d]";;
esac
