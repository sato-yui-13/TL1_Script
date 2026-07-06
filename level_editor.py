import bpy
import math
import bpy_extras
import gpu
import gpu_extras.batch
import copy
import mathutils


# ブレンダー登録情報
bl_info = {
    "name": "レベルエディタ",
    "author": "satou yui",
    "version": (1, 0),
    "blender": (3, 3, 1),
    "location": "",
    "description": "レベルエディタ",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Object"
}


# メニュー
def draw_menu_manual(self, context):
    self.layout.operator("wm.url_open_preset", text="Manual", icon='HELP')


class TOPBAR_MT_my_menu(bpy.types.Menu):
    bl_idname = "TOPBAR_MT_my_menu"
    bl_label = "MyMenu"
    bl_description = "拡張メニュー by " + bl_info["author"]

    def draw(self, context):
        self.layout.operator(MYADDON_OT_stretch_vertex.bl_idname,
                             text=MYADDON_OT_stretch_vertex.bl_label)
        self.layout.operator(MYADDON_OT_create_ico_sphere.bl_idname,
                             text=MYADDON_OT_create_ico_sphere.bl_label)
        self.layout.operator(MYADDON_OT_export_scene.bl_idname,
                             text=MYADDON_OT_export_scene.bl_label)


    def submenu(self, context):
        self.layout.menu(TOPBAR_MT_my_menu.bl_idname)


# 頂点操作
class MYADDON_OT_stretch_vertex(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_stretch_vertex"
    bl_label = "頂点を伸ばす"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.data.objects["Cube"].data.vertices[0].co.x += 1.0
        return {'FINISHED'}


# ICO球生成
class MYADDON_OT_create_ico_sphere(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_create_ico_sphere"
    bl_label = "ICO球生成"

    def execute(self, context):
        bpy.ops.mesh.primitive_ico_sphere_add()
        return {'FINISHED'}


# シーン出力
class MYADDON_OT_export_scene(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname = "myaddon.myaddon_ot_export_scene"
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

    def write_and_print(self, file, text):
        file.write(text + "\n")

    def parse_scene_recursive(self, file, obj, level):

        indent = "\t" * level

        self.write_and_print(file, indent + obj.type)

        trans, rot, scale = obj.matrix_local.decompose()
        rot = rot.to_euler()

        rot.x = math.degrees(rot.x)
        rot.y = math.degrees(rot.y)
        rot.z = math.degrees(rot.z)

        self.write_and_print(file, indent + f"T {trans.x} {trans.y} {trans.z}")
        self.write_and_print(file, indent + f"R {rot.x} {rot.y} {rot.z}")
        self.write_and_print(file, indent + f"S {scale.x} {scale.y} {scale.z}")

        if "file_name" in object:
            self.write_and_print(file, indent + f"N {obj['file_name']}")

        self.write_and_print(file, indent + "END\n")

        #カスタムプログラムパティ'collision'
        #カスタムプロパティ collision
        if "collider" in object:
            self.write_and_print(file, indent + "C %s" % object["collider"])

            temp_str = indent + "CC %f %f %f"
            temp_str %= (object["collider_center"][0], object["collider_center"][1], object["collider_center"][2])
            self.write_and_print(file, temp_str)

            temp_str = indent + "CS %f %f %f"
            temp_str %= (object["collider_size"][0],object["collider_size"][1],object["collider_size"][2])
            self.write_and_print(file, temp_str)


        for child in obj.children:
            self.parse_scene_recursive(file, child, level + 1)


# ファイル名パネル
class OBJECT_PT_file_name(bpy.types.Panel):
    bl_idname = "OBJECT_PT_file_name"
    bl_label = "FileName"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        self.layout.operator(MYADDON_OT_stretch_vertex.bl_idname)
        self.layout.operator(MYADDON_OT_create_ico_sphere.bl_idname)
        self.layout.operator(MYADDON_OT_export_scene.bl_idname)


        obj = context.object

        if obj:
            if "file_name" in obj:
                self.layout.prop(obj, '["file_name"]', text="FileName")
            else:
                self.layout.operator(MYADDON_OT_add_filename.bl_idname)


# file_name追加
class MYADDON_OT_add_filename(bpy.types.Operator):
    bl_idname = "myaddon.myaddon_ot_add_filename"
    bl_label = "FileName追加"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        context.object["file_name"] = ""
        return {"FINISHED"}


# コライダー描画
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

        size = [2, 2, 2]

        # 頂点生成
        for obj in bpy.context.scene.objects:

            #コライダープロパティがなければ、描画をスキップ
            if not "collider" in object:
                continue
            #中心点、サイズの変数を宣言
            center=mathutils.Vector((0,0,0))
            size = mathutils.Vector((2,2,2))

            #プロパティから値を取得
            center[0]=object["collider_center"][0]
            center[1]=object["collider_center"][1]
            center[2]=object["cokkider_center"][2]
            size[0]=object["collider_size"][0]
            size[1]=object["collider_size"][1]
            size[2]=object["collider_size"][2]

            

           #追加前の頂点数
            start = len(vertices["pos"])

            for offset in offsets:
                pos = copy.copy(center)
                pos[0] += offset[0] * size[0]
                pos[1] += offset[1] * size[1]
                pos[2] += offset[2] * size[2]
                #ローカル座標からワールド座標に変換
                pos=object.mtrix_world @ pos
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



#オペレータ　カスタム　プロパティ['collider']追加
class MYADDON_OT_add_collider(bpy.types.Operator):
    bl_idname="myaddon.myaddon_ot_add_collider"
    bl_label="コライダー 追加"
    bl_description="['collider']カスタムプロパティを追加します"
    bl_options={"REGISTER","UNDO"}


    def execute(self,context):

        #['collider']カスタムプロパティを追加
        context.object["collider"]="BOX"
        context.object["collider_center"]=mathutils.Vector((0,0,0))
        context.object["collider_size"]=mathutils.Vector((2,2,2))

        return{"FINISHED"}

#パネル クラス
class OBJECT_PT_collider(bpy.types.Panel):
    bl_idname = "OBJECT_PT_collider"
    bl_label = "Collider"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    # サブメニューの描画
    def draw(self, context):

        #パネルに項目を追加
        if "collider" in context.object:
            #既にプロパティがあれば、プロパティを表示
            self.layout.prop(context.object, '["collider"]', text="Type")
            self.layout.prop(context.object, '["collider_center"]', text="Center")
            self.layout.prop(context.object, '["collider_size"]', text="Size")
        else:
            #プロパティがなければ、プロパティ追加ボタンを表示
            self.layout.operator(MYADDON_OT_add_collider.bl_idname, text="コライダー追加")
           

# 登録クラス
classes = (
    MYADDON_OT_stretch_vertex,
    MYADDON_OT_create_ico_sphere,
    MYADDON_OT_export_scene,
    TOPBAR_MT_my_menu,
    MYADDON_OT_add_filename,
    OBJECT_PT_file_name,
    MYADDON_OT_add_collider,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_editor_menus.append(TOPBAR_MT_my_menu.submenu)

    DrawCollider.handle = bpy.types.SpaceView3D.draw_handler_add(
        DrawCollider.draw_collider, (), "WINDOW", "POST_VIEW"
    )


def unregister():

    bpy.types.TOPBAR_MT_editor_menus.remove(TOPBAR_MT_my_menu.submenu)

    bpy.types.SpaceView3D.draw_handler_remove(
        DrawCollider.handle, "WINDOW"
    )

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()