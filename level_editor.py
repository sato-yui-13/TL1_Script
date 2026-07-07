import bpy
import math
import bpy_extras
import gpu
import gpu_extras.batch
import copy
import mathutils


# =========================
# アドオン情報
# =========================
bl_info = {
    "name": "レベルエディタ",
    "author": "satou yui",
    "version": (1, 0),
    "blender": (3, 3, 1),
    "category": "Object"
}


# =========================
# メニュー
# =========================
class TOPBAR_MT_my_menu(bpy.types.Menu):
    bl_idname = "TOPBAR_MT_my_menu"
    bl_label = "MyMenu"

    def draw(self, context):
        self.layout.operator(MYADDON_OT_add_collider.bl_idname, text="Collider追加")
        self.layout.operator(MYADDON_OT_create_ico_sphere.bl_idname, text="ICO球生成")
        self.layout.operator(MYADDON_OT_export_scene.bl_idname, text="シーン出力")


# =========================
# Collider追加
# =========================
class MYADDON_OT_add_collider(bpy.types.Operator):
    bl_idname = "myaddon.add_collider"
    bl_label = "コライダー追加"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        obj = context.object
        if obj is None:
            return {"CANCELLED"}

        obj["collider"] = "BOX"
        obj["collider_center"] = (0.0, 0.0, 0.0)
        obj["collider_size"] = (2.0, 2.0, 2.0)

        return {"FINISHED"}


# =========================
# Collider UI
# =========================
class OBJECT_PT_collider(bpy.types.Panel):
    bl_idname = "OBJECT_PT_collider"
    bl_label = "Collider"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):

        obj = context.object

        if obj and "collider" in obj:

            self.layout.prop(obj, '["collider"]', text="Type")
            self.layout.prop(obj, '["collider_center"]', text="Center")
            self.layout.prop(obj, '["collider_size"]', text="Size")

        else:
            self.layout.operator(
                MYADDON_OT_add_collider.bl_idname,
                text="コライダー追加"
            )


# =========================
# シーン出力
# =========================
class MYADDON_OT_export_scene(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname = "myaddon.export_scene"
    bl_label = "シーン出力"
    filename_ext = ".scene"

    def execute(self, context):
        self.export()
        return {'FINISHED'}

    def export(self):

        with open(self.filepath, "wt") as file:
            file.write("SCENE\n")

            for obj in bpy.context.scene.objects:
                if obj.parent:
                    continue
                self.parse_scene_recursive(file, obj, 0)

    def write(self, file, text):
        file.write(text + "\n")

    def parse_scene_recursive(self, file, obj, level):

        indent = "\t" * level

        self.write(file, indent + obj.type)

        t, r, s = obj.matrix_local.decompose()
        r = r.to_euler()

        r = (math.degrees(r.x), math.degrees(r.y), math.degrees(r.z))

        self.write(file, indent + f"T {t.x} {t.y} {t.z}")
        self.write(file, indent + f"R {r[0]} {r[1]} {r[2]}")
        self.write(file, indent + f"S {s.x} {s.y} {s.z}")

        if "file_name" in obj:
            self.write(file, indent + f"N {obj['file_name']}")

        # collider export
        if "collider" in obj:

            c = obj["collider_center"]
            size = obj["collider_size"]

            self.write(file, indent + f"C {obj['collider']}")

            self.write(file, indent + f"CC {c[0]} {c[1]} {c[2]}")
            self.write(file, indent + f"CS {size[0]} {size[1]} {size[2]}")

        self.write(file, indent + "END")

        for child in obj.children:
            self.parse_scene_recursive(file, child, level + 1)


# =========================
# ICO球
# =========================
class MYADDON_OT_create_ico_sphere(bpy.types.Operator):
    bl_idname = "myaddon.create_ico_sphere"
    bl_label = "ICO球生成"

    def execute(self, context):
        bpy.ops.mesh.primitive_ico_sphere_add()
        return {'FINISHED'}


# =========================
# コライダー描画
# =========================
class DrawCollider:

    handle = None

    @staticmethod
    def draw_collider():

        shader = gpu.shader.from_builtin("UNIFORM_COLOR")

        vertices = {"pos": []}
        indices = []

        offsets = [
            [-0.5, -0.5, -0.5],
            [ 0.5, -0.5, -0.5],
            [-0.5,  0.5, -0.5],
            [ 0.5,  0.5, -0.5],
            [-0.5, -0.5,  0.5],
            [ 0.5, -0.5,  0.5],
            [-0.5,  0.5,  0.5],
            [ 0.5,  0.5,  0.5],
        ]

        for obj in bpy.context.scene.objects:

            if obj is None:
                continue

            if "collider" not in obj:
                continue

            center = mathutils.Vector(obj["collider_center"])
            size = mathutils.Vector(obj["collider_size"])

            start = len(vertices["pos"])

            for offset in offsets:
                pos = copy.copy(center)

                pos[0] += offset[0] * size[0]
                pos[1] += offset[1] * size[1]
                pos[2] += offset[2] * size[2]

                pos = obj.matrix_world @ pos
                vertices["pos"].append(pos)

            indices.extend([
                [start+0, start+1], [start+2, start+3],
                [start+0, start+2], [start+1, start+3],
                [start+4, start+5], [start+6, start+7],
                [start+4, start+6], [start+5, start+7],
                [start+0, start+4], [start+1, start+5],
                [start+2, start+6], [start+3, start+7],
            ])

        batch = gpu_extras.batch.batch_for_shader(
            shader, "LINES", vertices, indices=indices
        )

        shader.bind()
        shader.uniform_float("color", (0.5, 1.0, 1.0, 1.0))
        batch.draw(shader)


# =========================
# クラス登録
# =========================
classes = (
    MYADDON_OT_add_collider,
    OBJECT_PT_collider,
    MYADDON_OT_export_scene,
    MYADDON_OT_create_ico_sphere,
    TOPBAR_MT_my_menu,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    DrawCollider.handle = bpy.types.SpaceView3D.draw_handler_add(
        DrawCollider.draw_collider, (), "WINDOW", "POST_VIEW"
    )


def unregister():
    bpy.types.SpaceView3D.draw_handler_remove(
        DrawCollider.handle, "WINDOW"
    )

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()