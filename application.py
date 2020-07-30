import dash
import dash_html_components as html
import dash_core_components as dcc
import plotly.express as px
import pandas as pd
import pythena
import datetime
import json
import ast

app = dash.Dash(__name__)

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

athena_client = pythena.Athena("twitterappdatalake",region="ap-southeast-2")

# string_query='''
#     SELECT * FROM twitterappdatalake.aggregatedresultsforapp LIMIT 100
#     '''
# df_array = athena_client.execute(string_query)
# df=df_array[0]
df=pd.read_csv('sample_data.csv')
dffiltered=df[(df['partition_1']=='AMD') & (df['partition_0']=='Technology') ].sort_values(by=['create_date'],ascending=True)
partition_1_options=[]
for i in df['partition_1'].unique():
    partition_1_options.append({'label': i, 'value': i})
# partition_0_options=[]
# for i in df['partition_0'].unique():
#     partition_0_options.append({'label': i, 'value': i})


fig = px.line(dffiltered, x="create_date", y="avg_polarity", title='Sentiment over Time')

##Treemap of words
date_selected='2020-07-20'
df_wordthatdate=dffiltered[dffiltered['create_date']==date_selected]
word_freq_str=df_wordthatdate['word_freq'].iloc[0]
word_freq_arr=ast.literal_eval(word_freq_str)
df_wf=pd.DataFrame(word_freq_arr,columns=['word','freq'])
df_wf=df_wf.sort_values(by=['freq'],ascending=True)
fig_treemap = px.treemap(df_wf, path=['word'], values='freq',
                  color='freq',color_continuous_scale='blues', title='Word Frequency Map')

##APP LAYOUT
app.layout = html.Div([
    html.H1('Twitter Sentiment Application'),
    html.Div(id='dd-output-container'),
    dcc.Dropdown(
        id='demo-dropdown',
        options=partition_1_options,
        value='Australia'
    ),
    dcc.Graph(
    id='sentiment-graph',
    figure=fig
    ),
    dcc.Graph(
    id='word-freq',
    figure=fig_treemap
    )
])


@app.callback(
    [dash.dependencies.Output('sentiment-graph', 'figure'),
     dash.dependencies.Output('word-freq', 'figure')
    ],
    [dash.dependencies.Input('demo-dropdown', 'value')])
def update_output(value):
    dffiltered=df[(df['partition_1']==value) ].sort_values(by=['create_date'],ascending=True)
    fig = px.line(dffiltered, x="create_date", y="avg_polarity", title='Sentiment over Time')

    date_selected='2020-07-20'
    df_wordthatdate=dffiltered[dffiltered['create_date']==date_selected]
    word_freq_str=df_wordthatdate['word_freq'].iloc[0]
    word_freq_arr=ast.literal_eval(word_freq_str)
    df_wf=pd.DataFrame(word_freq_arr,columns=['word','freq'])
    df_wf=df_wf.sort_values(by=['freq'],ascending=True)
    fig_treemap = px.treemap(df_wf, path=['word'], values='freq',
                    color='freq',color_continuous_scale='blues', title='Word Frequency Map')
    return fig,fig_treemap


application = app.server

if __name__ == '__main__':
    application.run(debug=True, port=8080)