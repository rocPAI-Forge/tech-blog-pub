"""Minimal RAX Session surface used by the place controller (illustrative)."""

from labs.rax_drawer.rax_place.tools import Session
from labs.rax_drawer.rax_place.code.open_place_close.controller import main

# Explore while developing; switch to split="test" only after freeze.
with Session(split="explore", episode_limit_s=180.0) as ctx:
    ctx.reset(include_cameras=False)
    obs = ctx.observe(include_cameras=True)
    # obs: joints, camera_calibrations, cameras[top|side|wrist],
    #      depth_images["top"] (uint16 mm) — no drawer joint / cube pose.
    ctx.step({"vy": 0.02}, duration_s=0.25)
    print(ctx.check_success())

# Frozen program entry (explore self-test or locked eval):
# with Session(split="test") as ctx:
#     ok = main(ctx)
