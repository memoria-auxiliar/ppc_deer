import pandas as pd

from dash import Dash, dcc, html, Input, Output, State, dash_table
from dash.exceptions import PreventUpdate

def onoff_print(texto):
    if False:
        print(texto)

# Ler dados de entrada

dados = pd.read_excel('./dados/Tabela de Equivalências_DEER.xlsx', None)

df_ppc_1 = dados['PPC Anterior']
df_ppc_1['Disciplina'] = df_ppc_1['Disciplina'].str.strip()
df_ppc_1 = df_ppc_1.set_index('Disciplina')

df_ppc_2 = dados['PPC Atual']
df_ppc_2['Disciplina'] = df_ppc_2['Disciplina'].str.strip()
df_ppc_2 = df_ppc_2.set_index('Disciplina')

df_eqv = dados['Equivalências']
df_eqv['Disciplina_1'] = df_eqv['Disciplina_1'].str.strip()
df_eqv['Disciplina_2'] = df_eqv['Disciplina_2'].str.strip()

# # depuração
# onoff_print(f'df_ppc_1.head(5) = \n{df_ppc_1.head(5)}\n=====')
# onoff_print(f'df_ppc_2.head(5) = \n{df_ppc_2.head(5)}\n=====')
# onoff_print(f'df_eqv.head(5) = \n{df_eqv.head(5)}\n=====')
# breakpoint()

# ==============================================================================
# Dash App - Layout
# ==============================================================================

app = Dash(__name__, title='PPC DEER')
server = app.server
app.layout = html.Div(
    [
        html.Div(
            children=[
                dcc.Markdown(
                    children=[
                        f"""
                        ### Simulador de migração de PPC (versão 0.0 - 31/03/2023)
                        Desenvolvido por **CEAR_Aplicações_e_Dados**
                        """
                    ],
                    className="twelve columns column_style",
                ),
            ],
            className="row row_style",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.H6('Disciplinas do PPC Anterior'),
                        dcc.Checklist(
                            id=f'checklist_ppc_1',
                            options=[
                                {'label': f'{periodo} - {disciplina} - {creditos} créditos', 'value': disciplina}
                                for periodo, disciplina, creditos in zip(df_ppc_1['Período'], df_ppc_1.index, df_ppc_1['Créditos'])
                            ],
                            # depuração: marcar todas as check
                            # value=df_ppc_1.index,
                        ),
                    ],
                    className="six columns column_style_sem_center zera_margin-left",
                ),
                html.Div(
                    children=[dcc.Markdown(id='markdown_ppc_2')],
                    className="six columns column_style_sem_center",
                ),
            ],
            className="row row_style",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[dcc.Markdown(id='markdown_resumo')],
                    className="twelve columns column_style_sem_center",
                )
            ],
            className="row row_style",
        ),
    ]
)

# ==============================================================================
# Dash App - Callbacks
# ==============================================================================

@app.callback(
    Output('markdown_ppc_2', 'children'),
    Output('markdown_resumo', 'children'),
    Input('checklist_ppc_1', 'value'),
)
def gera_markdown_de_todas_as_categorias(checklist_values):

    if checklist_values is None:
        raise PreventUpdate

    onoff_print(f'gera_markdown_de_todas_as_categorias:')
    onoff_print(f'checklist_values = {checklist_values}')

    # Percorrer equivalencias em busca de match...
    list_match = []
    for _, row_eqv in df_eqv.iterrows():

        # Pegar disciplinas no ppc_1
        d1 = row_eqv['Disciplina_1'].split('&&')
        d1 = [item.strip() for item in d1]

        # Se todos os elementos de d1 estiverem marcados, ocorre um match!
        list_d1_ok = [(disciplina in checklist_values) for disciplina in d1]

        # depuração
        onoff_print(f'd1 = {d1}\n')
        onoff_print(f'list_d1_ok = {list_d1_ok}\n')

        if all(list_d1_ok):

            # Pegar disciplinas no ppc_2
            d2 = row_eqv['Disciplina_2'].split('&&')
            d2 = [item.strip() for item in d2]

            # depuração
            onoff_print(f'd1 = {d1}\n')
            onoff_print(f'list_d1_ok = {list_d1_ok}\n')
            onoff_print(f'd2 = {d2}\n')

            # Percorrer disciplinas de d2...
            for disciplina in d2:

                # Localizar no ppc_2 
                row_ppc_2 = df_ppc_2.loc[disciplina]
                onoff_print(f'row_ppc_2 = \n{row_ppc_2}\n')

                # Pegar (periodo, credito e extensão), mas evitando duplicidades...
                jah_dispensou = [(disciplina == item['Disciplina']) for item in list_match]
                if any(jah_dispensou):
                    continue
                list_match.append(
                    {
                        'Período': row_ppc_2['Período'],
                        'Disciplina': disciplina,
                        'CH': row_ppc_2['CH'],
                        'Créditos': row_ppc_2['Créditos'],
                        'Extensão': row_ppc_2['Extensão'],
                    }
                )

    # Ordenar 'list_match' para ficar na mesma ordem do ppc anterior
    minha_ordem = {
        '1° período': 1, '2° período': 2, '3° período': 3, '4° período': 4, '5° período': 5,
        '6° período': 6, '7° período': 7, '8° período': 8, '9° período': 9, '10° período': 10,
        'Conteúdos Complementares Flexíveis': 11, 'Optativas': 12,
    }
    list_match = sorted(list_match, key=lambda item: minha_ordem[item['Período']]) 

    # Converte 'list_match' em formato de texto
    texto_1 = '###### Aproveitamentos do PPC Atual\n'
    for item in list_match:
        texto_1 += f"* {item['Período']} - {item['Disciplina']} - {item['CH']} horas - {item['Créditos']} crédito(s) - {item['Extensão']} horas de Extensão\n"

    # Construir o resumo
    total_disciplinas = 0
    total_creditos = 0
    texto_2 = '##### Resumo dos Aproveitamentos\n'
    for periodo in minha_ordem.keys():
        aux = [item['Créditos'] for item in list_match if item['Período'] == periodo]
        texto_2 += f'* {periodo}: {len(aux)} disciplina(s) dispensada(s), totalizando **{sum(aux)} crédito(s)**\n'
        total_disciplinas += len(aux)
        total_creditos += sum(aux)
    texto_2 += f'##### Totais: {total_disciplinas} disciplina(s) dispensada(s), totalizando **{total_creditos} crédito(s)**'

    return texto_1, texto_2

if __name__ == '__main__':
    app.run_server(debug=False)
