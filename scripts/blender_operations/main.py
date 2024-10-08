"""
1. Ajuste de Rotação e Posição: Rotaciona o objeto em três eixos (X, Y, Z) e ajusta sua posição para que a parte mais baixa toque o plano do chão (z=0).
2. Seleção e Deleção de Vértices Dentro de uma Circunferência: Seleciona vértices dentro de uma circunferência especificada e, em seguida, inverte a seleção para deletar aqueles fora da circunferência.
3. Corte Booleano com um Cubo: Cria um cubo que serve como cortador para modificar o objeto principal através de uma operação booleana de diferença, seguido pela remoção do cortador.
"""

import bpy
import bmesh
import math

def ajustar_objeto(nome_do_objeto, angulo_x, angulo_y, angulo_z):
    obj = bpy.data.objects[nome_do_objeto]

    # Ajusta rotação do objeto
    obj.rotation_euler.x = math.radians(angulo_x)
    obj.rotation_euler.y = math.radians(angulo_y)
    obj.rotation_euler.z = math.radians(angulo_z)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

    # Ajusta a posição do objeto para que a parte mais baixa toque o plano do chão (z=0)
    lowest_point = min(vertex.co.z for vertex in obj.data.vertices)
    obj.location.z -= lowest_point

    bpy.context.view_layer.update()

def selecionar_vertices_dentro_da_circunferencia(nome_do_objeto, cx, cy, raio):
    obj = bpy.data.objects[nome_do_objeto]

    bpy.ops.object.mode_set(mode='OBJECT')
    mesh = obj.data
    for vertex in mesh.vertices:
        global_vertex_location = obj.matrix_world @ vertex.co
        dist = math.sqrt((global_vertex_location.x - cx) ** 2 + (global_vertex_location.y - cy) ** 2)
        if dist <= raio:
            vertex.select = True

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='INVERT')
    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.object.mode_set(mode='OBJECT')

def cortar_objeto(nome_do_objeto, posicao_z_cortador, escala_x_cortador, escala_y_cortador, escala_z_cortador):
    objeto_a_cortar = bpy.data.objects[nome_do_objeto]

    # Cria e posiciona o cortador
    bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, location=(0, 0, 0))
    cortador = bpy.context.object
    cortador.location.z = posicao_z_cortador
    cortador.scale.x = escala_x_cortador
    cortador.scale.y = escala_y_cortador
    cortador.scale.z = escala_z_cortador

    # Aplica corte booleano
    mod_bool = objeto_a_cortar.modifiers.new(type="BOOLEAN", name="Corte")
    mod_bool.object = cortador
    mod_bool.operation = 'DIFFERENCE'
    bpy.context.view_layer.update()

    # Aplica o modificador booleano e remove o cortador
    bpy.context.view_layer.objects.active = objeto_a_cortar
    bpy.ops.object.modifier_apply(modifier="Corte")
    bpy.data.objects.remove(cortador)
    
def suavizar_superficie(nome_do_objeto, niveis_de_subdivisao, intensidade_suavizacao):
    obj = bpy.data.objects[nome_do_objeto]

    # Aplica o modificador Subdivision Surface
    mod_subdiv = obj.modifiers.new(name="Subdivisao", type="SUBSURF")
    mod_subdiv.levels = niveis_de_subdivisao
    mod_subdiv.render_levels = niveis_de_subdivisao
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="Subdivisao")

    # Aplica o modificador Smooth
    mod_smooth = obj.modifiers.new(name="Suavizar", type="SMOOTH")
    mod_smooth.factor = intensidade_suavizacao
    # Número de vezes para suavizar a malha. Ajuste conforme necessário.
    mod_smooth.iterations = 10
    bpy.ops.object.modifier_apply(modifier="Suavizar")



def otimizar_malha(nome_do_objeto, modo_de_otimizacao, valor_de_otimizacao):
    obj = bpy.data.objects[nome_do_objeto]
    bpy.context.view_layer.objects.active = obj

    # Adiciona o modificador Decimate
    mod_decimate = obj.modifiers.new(name="OtimizarMalha", type="DECIMATE")

    # Configura o modificador de acordo com o modo de otimização desejado
    if modo_de_otimizacao == 'COLLAPSE':
        # Modo COLLAPSE: Reduz a contagem de polígonos pela porcentagem fornecida (0 a 1)
        mod_decimate.ratio = valor_de_otimizacao
    elif modo_de_otimizacao == 'UNSUBDIV':
        # Modo UNSUBDIV: Desfaz a subdivisão em uma quantidade específica de vezes
        mod_decimate.iterations = int(valor_de_otimizacao)
    elif modo_de_otimizacao == 'DISSOLVE':
        # Modo DISSOLVE: Usa o ângulo para dissolver arestas planas
        mod_decimate.angle_limit = valor_de_otimizacao
        mod_decimate.decimate_type = 'DISSOLVE'

    # Aplica o modificador
    bpy.ops.object.modifier_apply(modifier="OtimizarMalha")


def preencher_buracos(nome_do_objeto, tamanho_maximo=0):
    obj = bpy.data.objects[nome_do_objeto]
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.fill_holes(sides=tamanho_maximo)
    bpy.ops.object.mode_set(mode='OBJECT')

def corrigir_normais(nome_do_objeto):
    obj = bpy.data.objects[nome_do_objeto]
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    

def ajustar_escala(nome_do_objeto, tamanho_desejado):
    obj = bpy.data.objects[nome_do_objeto]
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    
    # Calcula a maior dimensão atual do objeto
    dimensoes_atuais = obj.dimensions
    maior_dimensao = max(dimensoes_atuais)

    # Calcula o fator de escala necessário para ajustar a maior dimensão ao tamanho desejado
    fator_de_escala = tamanho_desejado / maior_dimensao

    # Aplica o fator de escala
    obj.scale *= fator_de_escala
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


if __name__ == '__main__':
    nome_do_objeto = "mesh"
    cx, cy = 0.0, 0.0
    raio = 0.4
    angulo_x, angulo_y, angulo_z = 180, 180, 0
    posicao_z_cortador = -1
    escala_x_cortador, escala_y_cortador, escala_z_cortador = 10, 10, 1.1

    ajustar_objeto(nome_do_objeto, angulo_x, angulo_y, angulo_z)
    selecionar_vertices_dentro_da_circunferencia(nome_do_objeto, cx, cy, raio)
    cortar_objeto(nome_do_objeto, posicao_z_cortador, escala_x_cortador, escala_y_cortador, escala_z_cortador)
    suavizar_superficie(nome_do_objeto, 2, 0.5)
    otimizar_malha(nome_do_objeto, 'COLLAPSE', 0.5)
    preencher_buracos(nome_do_objeto)
    corrigir_normais(nome_do_objeto)
    ajustar_escala(nome_do_objeto, 10.0)