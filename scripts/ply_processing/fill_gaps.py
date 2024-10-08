from plyfile import PlyData, PlyElement
import numpy as np
from sklearn.neighbors import NearestNeighbors
import os

def carregar_arquivo_ply(caminho_arquivo):
    """Carrega o arquivo .ply e extrai os dados dos vértices."""
    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"O arquivo {caminho_arquivo} não foi encontrado.")

    plydata = PlyData.read(caminho_arquivo)
    vertex_data = plydata['vertex'].data
    points = np.vstack([vertex_data['x'], vertex_data['y'], vertex_data['z']]).T

    # Identifica campos extras, como cores
    campos_extras = [name for name in vertex_data.dtype.names if name not in ('x', 'y', 'z')]

    # Extrai dados extras como cores
    dados_extras = {campo: vertex_data[campo] for campo in campos_extras}

    if points.size == 0:
        raise ValueError("A nuvem de pontos está vazia.")

    return points, dados_extras, campos_extras, plydata

def identificar_pontos_vazios(points, n_neighbors=50):
    """Identifica pontos vazios com base na média das distâncias aos vizinhos."""
    nbrs = NearestNeighbors(n_neighbors=n_neighbors).fit(points)
    distances, indices = nbrs.kneighbors(points)
    limiar_distancia = np.mean(distances) + 2 * np.std(distances)
    pontos_vazios = distances.mean(axis=1) > limiar_distancia

    return pontos_vazios, indices

def adicionar_novos_pontos(points, pontos_vazios, indices, dados_extras, n_pontos_adicionais=5):
    """Adiciona novos pontos em áreas de baixa densidade."""
    novos_pontos = []
    novos_dados_extras = {campo: [] for campo in dados_extras.keys()}

    for idx, is_vazio in enumerate(pontos_vazios):
        if is_vazio:
            vizinhos = points[indices[idx]]
            vizinhos_extras = {campo: dados_extras[campo][indices[idx]] for campo in dados_extras}
            centroide = np.mean(vizinhos, axis=0)

            for _ in range(n_pontos_adicionais):
                deslocamento = centroide - points[idx]
                novo_ponto = points[idx] + np.random.uniform(0.1, 0.4) * deslocamento

                if np.linalg.norm(novo_ponto - centroide) < 0.05:
                    novos_pontos.append(novo_ponto)
                    for campo in dados_extras:
                        novo_valor_extra = np.mean(vizinhos_extras[campo], axis=0)
                        novos_dados_extras[campo].append(novo_valor_extra)

    return np.array(novos_pontos), novos_dados_extras

def salvar_arquivo_ply(points, dados_extras, campos_extras, plydata, caminho_saida):
    """Salva os pontos e dados extras atualizados em um novo arquivo .ply."""
    arrays_para_registrar = [points[:, 0], points[:, 1], points[:, 2]]
    for campo in campos_extras:
        arrays_para_registrar.append(dados_extras[campo])

    new_vertex_data = np.core.records.fromarrays(
        arrays_para_registrar,
        names=plydata['vertex'].data.dtype.names
    )

    vertex_element = PlyElement.describe(new_vertex_data, 'vertex')
    plydata_updated = PlyData([vertex_element], text=False)
    plydata_updated.write(caminho_saida)

    print(f"Preenchimento concluído e salvo no arquivo {caminho_saida}.")

def processar_ply(caminho_entrada, caminho_saida, n_neighbors=50, n_pontos_adicionais=5):
    """Pipeline completo para adicionar pontos a arquivos .ply."""
    points, dados_extras, campos_extras, plydata = carregar_arquivo_ply(caminho_entrada)
    pontos_vazios, indices = identificar_pontos_vazios(points, n_neighbors)
    novos_pontos, novos_dados_extras = adicionar_novos_pontos(points, pontos_vazios, indices, dados_extras, n_pontos_adicionais)

    if len(novos_pontos) > 0:
        points = np.vstack([points, novos_pontos])
        for campo in campos_extras:
            dados_extras[campo] = np.hstack([dados_extras[campo], novos_dados_extras[campo]])

    salvar_arquivo_ply(points, dados_extras, campos_extras, plydata, caminho_saida)

if __name__ == "__main__":
    caminho_entrada = "/home/vicrrs/Downloads/IMG_4738/splat.ply"
    caminho_saida = "/home/vicrrs/LAMIA_projects/reconstructionPlys/splat_filled008.ply"
    processar_ply(caminho_entrada, caminho_saida)
