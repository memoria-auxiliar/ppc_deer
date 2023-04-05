import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dash import Dash, Input, Output, State, dash_table, dcc, html
from dash.exceptions import PreventUpdate


def onoff_print(texto):
    if False:
        print(texto)

def montar_resumo_ppc(df_ppc, disciplinas_ok, CH_optativa):

    onoff_print(f'montar_resumo_ppc:')

    minha_ordem = [
        '1° período', 
        '2° período', 
        '3° período', 
        '4° período', 
        '5° período',
        '6° período', 
        '7° período', 
        '8° período', 
        '9° período', 
        '10° período',
        'Flexíveis', 
        'Optativas',
    ]

    aux = []
    for item in minha_ordem:
        dff = df_ppc[df_ppc['Período'] == item]

        flag_cursada = [(idx in disciplinas_ok) for idx, row in dff.iterrows()]

        # Apenas "Optativas" tem créditos necessários: "CH_optativa".

        if item == 'Optativas':
            ch_cursada = sum(dff.loc[flag_cursada, 'CH'])
            ch_restante = (CH_optativa - ch_cursada) if (CH_optativa - ch_cursada) > 0 else 0
            perc_restante = 100*ch_restante/CH_optativa
            perc_cursada = 100 - perc_restante
        else:
            ch_cursada = sum(dff.loc[flag_cursada, 'CH'])
            ch_total = sum(dff['CH'])
            ch_restante = ch_total - ch_cursada
            perc_restante = 100*ch_restante/ch_total
            perc_cursada = 100*ch_cursada/ch_total

        aux.append(
            {
                'Tipo': item,
                'CH_cursada': ch_cursada, 
                '%_cursada': f'{perc_cursada:.2f}', 
                'CH_restante': ch_restante, 
                '%_restante': f'{perc_restante:.2f}', 
            }
        )

        if 'Extensão' in dff.columns:
            aux[-1]['Extensão'] = f"{sum(dff.loc[flag_cursada, 'Extensão'])} de {sum(dff['Extensão'])}"

    return pd.DataFrame(aux, index=minha_ordem)

def obter_lista_de_disciplinas_para_dispensa(df12, df1, df2):

    onoff_print(f'obter_lista_de_disciplinas_para_dispensa:')

    ret1 = []
    ret2 = []
    for idx, row in df12.iterrows():

            # obtém ocorrências de "idx" em df_eqv...
            d1 = [item.strip() for item in row['Disciplina_1'].split('&&')]
            d2 = [item.strip() for item in row['Disciplina_2'].split('&&')]

            ch1 = [df1.loc[item, 'CH'] for item in d1]
            ch2 = [df2.loc[item, 'CH'] for item in d2]

            if sum(ch1) < sum(ch2):
                aux = [item for item in d1 if item not in ret1]
                ret1.extend(aux)
                aux = [item for item in d2 if item not in ret2]
                ret2.extend(aux)
    return ret1, ret2

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

disc_com_aumento_1, disc_com_aumento_2 = \
    obter_lista_de_disciplinas_para_dispensa(df_eqv, df_ppc_1, df_ppc_2)

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
                        '''
                        ### Simulador de migração de PPC - DEER/CEAR
                        Versão 0.0 - 05/04/2023 - Desenvolvimento: CEARDados
                        '''
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
                                {
                                    'label': html.B(f'{periodo} - {disciplina} - {creditos} créditos*'), 
                                    'value': disciplina
                                }
                                if disciplina in disc_com_aumento_1
                                else
                                {
                                    'label': f'{periodo} - {disciplina} - {creditos} créditos', 
                                    'value': disciplina
                                }
                                for periodo, disciplina, creditos in zip(df_ppc_1['Período'], df_ppc_1.index, df_ppc_1['Créditos'])
                            ],
                            # # depuração: marcar todas as check
                            # value=df_ppc_1.index,
                        ),
                        html.Hr(),
                        html.B('* Significa que será preciso abrir processo de dispensa.'),
                    ],
                    className="six columns column_style_sem_center zera_margin-left",
                ),
                html.Div(
                    children=[
                        html.H6('Disciplinas do PPC Atual'),
                        dcc.Checklist(
                            id=f'checklist_ppc_2',
                            options=[
                                {
                                    'label': html.B(f'{periodo} - {disciplina} - {creditos} créditos*'), 
                                    'value': disciplina,
                                    'disabled': True,
                                }
                                if disciplina in disc_com_aumento_2
                                else
                                {
                                    'label': f'{periodo} - {disciplina} - {creditos} créditos', 
                                    'value': disciplina,
                                    'disabled': True,
                                }
                                for periodo, disciplina, creditos in zip(df_ppc_2['Período'], df_ppc_2.index, df_ppc_2['Créditos'])
                            ],
                        ),
                    ],
                    className="six columns column_style_sem_center",
                ),
            ],
            className="row row_style",
        ),
        html.Div(
            children=[
                html.Div(
                    id='div_resumo_ppc_1',
                    className="six columns column_style_sem_center zera_margin-left",
                ),
                html.Div(
                    id='div_resumo_ppc_2',
                    className="six columns column_style_sem_center",
                ),
            ],
            className="row row_style",
        ),
    ]
)

# ==============================================================================
# Dash App - Callbacks
# ==============================================================================

@app.callback(
    Output('checklist_ppc_2', 'value'),
    Output('div_resumo_ppc_1', 'children'),
    Output('div_resumo_ppc_2', 'children'),
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
                jah_dispensou = [(disciplina == item) for item in list_match]
                if any(jah_dispensou):
                    continue

                # Chegando aqui... "Dispensar disciplina"
                list_match.append(disciplina)

    # Construir os resumos
    resumo_ppc_1 = montar_resumo_ppc(df_ppc_1, checklist_values, 12*15)
    resumo_ppc_2 = montar_resumo_ppc(df_ppc_2, list_match, 22*15)

    # Construir as tabelas
    cursada = sum(resumo_ppc_1['CH_cursada'])
    restante = sum(resumo_ppc_1['CH_restante'])

    fig1 = go.Figure(
        data=[
            go.Bar(name='Cursada', x=resumo_ppc_1['Tipo'], y=resumo_ppc_1['CH_cursada']),
            go.Bar(name='Restante', x=resumo_ppc_1['Tipo'], y=resumo_ppc_1['CH_restante']),
        ]
    )
    fig1.update_layout(barmode='stack')
    fig1.update_layout(title_text=f"{cursada}h / {restante}h")
    fig1.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

    ret_1 = [
        html.H6('Resumo PPC Anterior (CH 3855h):'),
        # html.P(f"Carga horária: {cursada}h cursadas, {restante}h restantes"),
        # html.P(f"Créditos: {cursada/15:.0f} cursados, {restante/15:.0f} restantes"),
        dcc.Graph(
            figure=fig1,
        ),
        dash_table.DataTable(
            data = resumo_ppc_1.to_dict('records'),
            columns = [{"name": i, "id": i} for i in resumo_ppc_1.columns],
            style_table={'overflowX': 'auto'},
            style_as_list_view=True,
            style_cell={'textAlign': 'center'},
        ),
    ]

    cursada = sum(resumo_ppc_2['CH_cursada'])
    restante = sum(resumo_ppc_2['CH_restante'])

    fig2 = go.Figure(
        data=[
            go.Bar(name='Cursada', x=resumo_ppc_2['Tipo'], y=resumo_ppc_2['CH_cursada']),
            go.Bar(name='Restante', x=resumo_ppc_2['Tipo'], y=resumo_ppc_2['CH_restante']),
        ]
    )
    fig2.update_layout(barmode='stack')
    fig2.update_layout(title_text=f"{cursada}h / {restante}h")
    fig2.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

    ret_2 = [
        html.H6('Resumo PPC Atual (CH 3900h):'),
        # html.P(f"Carga horária: {cursada}h dispensadas, {restante}h restantes"),
        # html.P(f"Créditos: {cursada/15:.0f} dispensados, {restante/15:.0f} restantes"),
        dcc.Graph(
            figure=fig2,
        ),
        dash_table.DataTable(
            data = resumo_ppc_2.to_dict('records'),
            columns = [{"name": i, "id": i} for i in resumo_ppc_2.columns],
            style_table={'overflowX': 'auto'},
            style_as_list_view=True,
            style_cell={'textAlign': 'center'},
        ),
    ]

    return list_match, ret_1, ret_2

if __name__ == '__main__':
    app.run_server(debug=False)
    # app.run_server(debug=True, port=8050)
