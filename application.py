import dash
from tabulate import tabulate
import dash_html_components as html
import dash_core_components as dcc
import dash_table
import plotly.express as px
import pandas as pd
import pythena
from datetime import datetime, timedelta
import json
import ast
import s3fs
import os
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

def update_datatable(df,search_query_selected,create_date_selected):
    dffiltered=df[df['search_query'].isin([search_query_selected]) ].sort_values(by=['create_date'],ascending=True)
    df_wordthatdate=dffiltered[dffiltered['create_date']==create_date_selected]
    top_tweets_str=df_wordthatdate['top_tweets'].iloc[0]
    top_tweets_arr=ast.literal_eval(top_tweets_str)
    df_toptweets=pd.DataFrame(top_tweets_arr)
    df_toptweets['text']=df_toptweets['text'].str.strip()
    tablecolumns=[{'id': c, 'name': c} for c in df_toptweets.columns]

    return [df_toptweets.to_dict('records'),tablecolumns]

def update_map_fig(df,search_query_selected,create_date_selected):
    dffiltered=df[df['search_query'].isin([search_query_selected]) ].sort_values(by=['create_date'],ascending=True)
    df_wordthatdate=dffiltered[dffiltered['create_date']==create_date_selected]
    word_freq_str=df_wordthatdate['word_freq'].iloc[0]
    word_freq_arr=ast.literal_eval(word_freq_str)
    df_wf=pd.DataFrame(word_freq_arr,columns=['word','freq'])
    df_wf=df_wf.sort_values(by=['freq'],ascending=True)
    fig_treemap = px.treemap(df_wf, height=400, path=['word'], values='freq',
                    color='freq',color_continuous_scale='blues', title='Word Frequency Map')
    fig_treemap=fig_treemap.update_layout(plot_bgcolor='rgba(0, 0, 0, 0)',paper_bgcolor='rgba(0, 0, 0, 0)',margin=dict(l=80, r=10, t=80, b=30))
    return fig_treemap

def fetch_data(fs):
    ##generate list of files in folder 'data':
    file_exist_arr=[]
    for file in os.listdir('data'):
        file_exist_arr.append(file)
    file_exist_arr

    for file1 in fs.listdir('aggregatedresultsforapp'):
        file_name=file1['Key'].split('/')[-1]
        read_file_path=file1['Key']
        if file_name not in file_exist_arr:
            write_file_path='data/' + file_name
            fs.download(read_file_path,write_file_path)

    # Read the initial file
    df = pd.read_csv('data/'+'2020-07-14.csv')
    # Concatenate from then on
    for file in os.listdir('data'):
        dfcurrent=pd.read_csv('data/'+file)
        df=pd.concat([dfcurrent,df])
    df['create_date']=pd.to_datetime(df['create_date'])
    return df

app = dash.Dash(__name__,   external_stylesheets=[dbc.themes.SIMPLEX])

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True
app.title = 'The Tweet Sentiment Project'

with open("C:/Users/William Jiang/Documents/credentials.json") as f:
    d = json.load(f)
    cred_json=d["twitter_api"]
    s3_cred_json=d["s3-access"]
##auth using s3fs
fs = s3fs.S3FileSystem(anon=False, key=s3_cred_json['ACCESS_KEY_ID'], secret=s3_cred_json['SECRET_ACCESS_KEY'])

df=fetch_data(fs)



dffiltered=df[df['search_query'].isin(['#Australia'])  ].sort_values(by=['create_date'],ascending=True)

df_unique_query=df[['partition_1','partition_0','search_query']].drop_duplicates()
multiselect_options=[]
for index,row in df_unique_query.iterrows():
    label_string=row['partition_0'] + ' - ' + row['partition_1'] + ' (' + row['search_query'] + ')'
    multiselect_options.append({'label':label_string, 'value': row['search_query']})

#Initial conditions
create_date_selected=max(df['create_date'])
search_query_selected='#Australia'

#Initialize the charts
fig_treemap=update_map_fig(df=df,search_query_selected=search_query_selected,create_date_selected=create_date_selected)
[datatable_object,column_object]=update_datatable(df=df,search_query_selected=search_query_selected,create_date_selected=create_date_selected)

##APP LAYOUT
app.layout = html.Div([
    html.H1('The Tweet Sentiment Project'),
    html.P(['Click on a specific date on the graph to see the Word Frequency and Top Tweets from that search query. Created by:',html.A(" William Jiang", href='https://iamwilliamj.com', target="_blank")]),
    html.Div(id='dd-output-container'),
    dcc.Dropdown(
        id='demo-dropdown',
        options=multiselect_options,
        value=[search_query_selected],
        multi=True
    ),
    # html.Div(id='my-output'),
    dbc.Row([
        dbc.Col([
            dcc.Graph(
            id='sentiment-graph'
            )
        ], className="four columns")
    ,
        dbc.Col([
            dcc.Graph( 
            id='word-freq',figure=fig_treemap
            )
        ], className="two columns")
    ],className="row"),
    dbc.Row([
        dbc.Col([
            dash_table.DataTable(
            data=datatable_object,
            columns=column_object,
            id='tweettable',
            style_data={
            'whiteSpace': 'normal',
            'height': 'auto'
            },
            style_cell={'textAlign': 'left'},
            style_table={ 'height': '80%',
             'width': '90%'},
            # data=df_toptweets.to_dict('records'),
            # columns=[{'id': c, 'name': c} for c in df_toptweets.columns],
            page_size=8,
            sort_action='native',
            filter_action='native'
            )
        ], className="three columns")
        
    ],className="row", style={'padding': 20}),
    #     html.Div([
    #     dcc.Markdown("""
    #         **click Data**

    #         Mouse over values in the graph.
    #     """),
    #     html.Pre(id='click-data')
    # ],className='three columns')
], style={'padding': 10})


@app.callback(
    [
    dash.dependencies.Output('sentiment-graph', 'figure')
    ],
    [dash.dependencies.Input('demo-dropdown', 'value')])
def update_output(value):
    dffiltered=df[df['search_query'].isin(value) ].sort_values(by=['create_date'],ascending=True)

    fig = px.line(dffiltered, height=400, x="create_date", y="avg_polarity", title='Sentiment over Time', color='partition_1',custom_data=['partition_0','partition_1','create_date','search_query'])
    fig.update_layout(title='Sentiment over Time',
                   xaxis_title='Date',
                   yaxis_title='Avg. Polarity',plot_bgcolor='rgba(0, 0, 0, 0)',paper_bgcolor='rgba(0, 0, 0, 0)'
                   ,margin=dict(l=10, r=80, t=80, b=30)
)
    return [fig]

@app.callback(
    Output(component_id='my-output', component_property='children'),
    [Input(component_id='demo-dropdown', component_property='value')]
)
def update_output_div(input_value):
    return 'Output: {}'.format(input_value)

@app.callback(
    [dash.dependencies.Output('click-data', 'children')
    ],
    [Input('sentiment-graph', 'clickData')])
def display_click_data(clickData):
    return [json.dumps(clickData, indent=2)]

@app.callback(
    [
    dash.dependencies.Output('word-freq', 'figure')
    ],
    [Input('sentiment-graph', 'clickData')])
def change_map_click_data(clickData):
    customDataList=clickData['points'][0]['customdata']
    print(customDataList[0])
    print(clickData)
    partition_0_selected=customDataList[0]
    partition_1_selected=customDataList[1]
    create_date_selected=customDataList[2]
    search_query_selected=customDataList[3]
    fig_treemap=update_map_fig(df,search_query_selected,create_date_selected)

    return [fig_treemap]

@app.callback(
    [
    dash.dependencies.Output('tweettable', 'data'),
    dash.dependencies.Output('tweettable', 'columns')
    ],
    [Input('sentiment-graph', 'clickData')])
def change_table_click_data(clickData):
    customDataList=clickData['points'][0]['customdata']
    partition_0_selected=customDataList[0]
    partition_1_selected=customDataList[1]
    create_date_selected=customDataList[2]
    search_query_selected=customDataList[3]
    ###Change the datatable
    # dffiltered=df[df['search_query'].isin([search_query_selected]) ].sort_values(by=['create_date'],ascending=True)
    # df_wordthatdate=dffiltered[dffiltered['create_date']==create_date_selected]
    # top_tweets_str=df_wordthatdate['top_tweets'].iloc[0]
    # top_tweets_arr=ast.literal_eval(top_tweets_str)
    # df_toptweets=pd.DataFrame(top_tweets_arr)
    # df_toptweets['text']=df_toptweets['text'].str.strip()
    # tablecolumns=[{'id': c, 'name': c} for c in df_toptweets.columns]
    datatable_object=update_datatable(df,search_query_selected=search_query_selected,create_date_selected=create_date_selected)
    return datatable_object

application = app.server

if __name__ == '__main__':
    application.run(debug=True, port=8080)