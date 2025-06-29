# Scene Duration Display

import bpy
from bpy.props import IntProperty
from bpy.app.handlers import persistent

# --- Globals ---
is_self_updating = False
msgbus_owner = object()
# Cache to store the last known state of timeline properties.
previous_timeline_state = (None, None, None, None, None)

# --- Operators ---
class SCENE_OT_set_preview_in(bpy.types.Operator):
    """Set current frame as Preview Range Start and enable Preview Range"""
    bl_idname = "scene.set_preview_in"
    bl_label = "Set Preview In (I)"
    bl_description = "Enable Preview Range and set its start to the current frame"

    def execute(self, context):
        scene = context.scene
        scene.use_preview_range = True
        scene.frame_preview_start = scene.frame_current
        if scene.frame_preview_end < scene.frame_preview_start:
            scene.frame_preview_end = scene.frame_preview_start
        # Trigger an update check after the operator runs.
        check_and_update_duration(scene)
        self.report({'INFO'}, f"Preview Range In set to {scene.frame_preview_start}")
        return {'FINISHED'}


class SCENE_OT_set_preview_out(bpy.types.Operator):
    """Set current frame as Preview Range End and enable Preview Range"""
    bl_idname = "scene.set_preview_out"
    bl_label = "Set Preview Out (O)"
    bl_description = "Enable Preview Range and set its end to the current frame"

    def execute(self, context):
        scene = context.scene
        scene.use_preview_range = True
        scene.frame_preview_end = scene.frame_current
        if scene.frame_preview_start > scene.frame_preview_end:
            scene.frame_preview_start = scene.frame_preview_end
        # Trigger an update check after the operator runs.
        check_and_update_duration(scene)
        self.report({'INFO'}, f"Preview Range Out set to {scene.frame_preview_end}")
        return {'FINISHED'}

# --- Core Logic ---
def check_and_update_duration(scene):
    """
    Checks if duration-affecting properties have changed by comparing with
    a cached state. If so, triggers the update. This is the central update logic.
    """
    global previous_timeline_state
    if not scene:
        return

    current_state = (
        scene.use_preview_range,
        scene.frame_start,
        scene.frame_end,
        scene.frame_preview_start,
        scene.frame_preview_end
    )

    if current_state != previous_timeline_state:
        previous_timeline_state = current_state
        update_timeline_duration_from_scene(scene)

@persistent
def on_frame_change_post(scene, depsgraph):
    """Handler for frame changes (e.g., scrubbing, playback)."""
    check_and_update_duration(scene)

def on_msgbus_notify():
    """Callback for msgbus property changes."""
    check_and_update_duration(bpy.context.scene)

def setup_msgbus():
    """Clear and set up the message bus subscriptions."""
    global msgbus_owner
    bpy.msgbus.clear_by_owner(msgbus_owner)
    msgbus_owner = object()

    # Subscribe to properties that are changed directly via the UI.
    props = [
        "frame_start", "frame_end", "use_preview_range",
        "frame_preview_start", "frame_preview_end"
    ]
    for prop in props:
        key = (bpy.types.Scene, prop)
        bpy.msgbus.subscribe_rna(
            key=key,
            owner=msgbus_owner,
            args=(),
            notify=on_msgbus_notify,
        )

def update_timeline_duration_from_scene(scene):
    """Calculates and updates the timeline_duration property."""
    global is_self_updating
    if not scene or is_self_updating:
        return

    is_self_updating = True
    try:
        start_f, end_f = (scene.frame_preview_start, scene.frame_preview_end) if scene.use_preview_range else (scene.frame_start, scene.frame_end)
        new_duration = max(1, end_f - start_f + 1)
        if scene.timeline_duration != new_duration:
            scene.timeline_duration = new_duration
    except Exception as e:
        print(f"[Scene Duration Display] update error: {e}")
    finally:
        is_self_updating = False

def duration_prop_update(self, context):
    """Called when the user manually changes the duration property."""
    global is_self_updating
    if is_self_updating:
        return
    is_self_updating = True
    try:
        scene = self
        duration = max(1, scene.timeline_duration)
        scene.timeline_duration = duration
        if scene.use_preview_range:
            scene.frame_preview_end = scene.frame_preview_start + duration - 1
        else:
            scene.frame_end = scene.frame_start + duration - 1
        # Trigger an update check after the user changes the duration.
        check_and_update_duration(scene)
    except Exception as e:
        print(f"[Scene Duration Display] duration update error: {e}")
    finally:
        is_self_updating = False

def initial_sync():
    """Function to be called by a timer for the initial sync."""
    check_and_update_duration(bpy.context.scene)
    return None

@persistent
def on_file_loaded_callback(dummy):
    """Handler for file load. Resets msgbus and triggers an initial sync."""
    setup_msgbus()
    if bpy.app.timers.is_registered(initial_sync):
        bpy.app.timers.unregister(initial_sync)
    bpy.app.timers.register(initial_sync, first_interval=0.1)

# --- UI ---
def draw_duration_in_header(self, context):
    space = context.space_data
    if space.type != 'DOPESHEET_EDITOR' or space.mode != 'TIMELINE':
        return
    layout = self.layout
    scene = context.scene
    if not scene:
        return
    layout.separator(factor=1.0)
    row = layout.row(align=True)
    row.operator(SCENE_OT_set_preview_in.bl_idname, text="I<")
    row.prop(scene, "timeline_duration", text="")
    row.operator(SCENE_OT_set_preview_out.bl_idname, text=">O")

# --- Registration ---
classes = (SCENE_OT_set_preview_in, SCENE_OT_set_preview_out)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.timeline_duration = IntProperty(
        name="Duration",
        default=100,
        min=1,
        update=duration_prop_update,
    )
    
    setup_msgbus()
    bpy.app.handlers.load_post.append(on_file_loaded_callback)
    bpy.app.handlers.frame_change_post.append(on_frame_change_post) # Add the new handler
    bpy.types.DOPESHEET_HT_header.append(draw_duration_in_header)
    bpy.app.timers.register(initial_sync, first_interval=0.01)

def unregister():
    if bpy.app.timers.is_registered(initial_sync):
        bpy.app.timers.unregister(initial_sync)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    bpy.msgbus.clear_by_owner(msgbus_owner)

    # Remove handlers
    if on_file_loaded_callback in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(on_file_loaded_callback)
    if on_frame_change_post in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(on_frame_change_post)

    try:
        bpy.types.DOPESHEET_HT_header.remove(draw_duration_in_header)
    except Exception:
        pass

    if hasattr(bpy.types.Scene, "timeline_duration"):
        del bpy.types.Scene.timeline_duration