
flake() {
    # podman  run --rm -v $(pwd)/app:/app:z -w /app python:3.8 flake8
    # podman compose run --rm app /app/python flake8
    # podman compose run --build --rm app sh -c "PYTHONPATH=/py/lib/python3.13/site-packages /py/bin/flake8"
    podman compose run --rm app sh -c "PYTHONPATH=/py/lib/python3.13/site-packages /py/bin/flake8"
}

exec-c () {
    podman compose run --rm app sh -c $@
}
exec-up () {
    podman compose up
}
# exec () {
#     echo $@
# }