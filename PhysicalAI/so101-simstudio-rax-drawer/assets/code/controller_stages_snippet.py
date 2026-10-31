"""Stage handoff in the frozen place controller (abbreviated from upstream).

Source: labs/rax_drawer/rax_place/code/open_place_close/controller.py
"""

def main(ctx) -> bool:
    ctx.reset(include_cameras=False)
    grasp = open_drawer(ctx)          # A–B: perceive handle, velocity pull, record pull/grasp_xy
    if grasp is None:
        return bool(ctx.check_success().get("success"))
    pick_and_place(ctx, grasp)        # C–E: fold-face → Jacobian pick → place 5.5 cm behind handle
    return close_drawer(ctx, grasp)   # F: pitch away, wrist-lock servo, push to recorded grasp_xy


# open_drawer returns geometry used later — not the drawer joint:
#   {"point": opened_handle_xyz, "pull": unit_xy, "grasp_xy": pinch_xy_at_open}
