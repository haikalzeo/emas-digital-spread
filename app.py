import json
import pytz
import requests
import cloudscraper
import pandas as pd
import plotly.express as px
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import streamlit as st
import plotly.graph_objects as go



############ Define time ############
current_datetime_utc = datetime.now(pytz.utc)
jakarta_timezone = pytz.timezone('Asia/Jakarta')
datetime_jakarta = current_datetime_utc.astimezone(jakarta_timezone)



############ Define dataframe ############
columns=['Platform','Buy', 'Sell', 'Spread', 'Date']
latest_spread_df = pd.DataFrame(columns=columns)
pluang_df = pd.DataFrame(columns=columns)
indogold_df = pd.DataFrame(columns=columns)
treasury_df = pd.DataFrame(columns=columns)
pegadaian_df = pd.DataFrame(columns=columns)
lakuemas_df = pd.DataFrame(columns=columns)


############ Define functions ############
def clean_currency(text):
  text = ''.join(filter(str.isdigit, text))
  return int(text)

def insert_data(df, platform, buy, sell, date, is_cleaned=False):
  if not is_cleaned:
    buy = clean_currency(buy)
    sell = clean_currency(sell)
  spread = round(((buy - sell) / buy ) * 100, 4)
  new_row = {
    'Platform': platform,
    'Buy': buy if platform == 'Brankaslm' else f'Rp{buy:,.0f}',
    'Sell': sell if platform == 'Brankaslm' else f'Rp{sell:,.0f}',
    'Spread': spread,
    'Date': date
  }
  if df.empty:
      df = pd.DataFrame([new_row])
  else:
      df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
  return df

def insert_latest_data(df, platform_df):
  new_row = platform_df.sort_values(by='Date').iloc[-1]
  new_row['Buy'] = int(new_row['Buy'].replace('Rp', '').replace(',', ''))
  new_row['Sell'] = int(new_row['Sell'].replace('Rp', '').replace(',', ''))
  if df.empty:
      df = pd.DataFrame([new_row])
  else:
      df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
  return df

def format_datetime(dt_with_tz):
  # Remove the timezone information
  dt_without_tz = dt_with_tz.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)

  # Format the datetime to string without microseconds
  formatted_date = dt_without_tz.strftime('%Y-%m-%d %H:%M:%S')
  return str(formatted_date)

def convert_to_jakarta_date(date_str):
  # Remove timezone info if exists and parse the date
  date_str = date_str.split('+')[0].split('Z')[0]
  date_object = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%f')

  # Make datetime object timezone aware
  utc_timezone = pytz.utc
  date_object = utc_timezone.localize(date_object)

  # Convert to Jakarta timezone
  date_object = date_object.astimezone(jakarta_timezone)

  # Format the date
  formatted_date = format_datetime(date_object)
  return formatted_date

def plot_gold_spread(df, platform_name):
    # Sort the dataframe by date in ascending order
    df_sorted = df.sort_values(by='Date')

    # Create the chart
    fig = px.line(df_sorted,
                  x='Date',
                  y='Spread',
                  # title=f'{platform_name} Gold Spread Over Time',
                  title=' ',
                  labels={'Date': 'Date', 'Spread': 'Spread'},
                  hover_data=['Buy', 'Sell'])

    fig.update_traces(line=dict(color='gold', width=3))
    fig.update_layout(
        margin=dict(t=25, b=0),
        xaxis_title=None,
        yaxis_title=None,
        plot_bgcolor='rgba(0, 0, 0, 0)',  # Transparent background
        paper_bgcolor='rgba(0, 0, 0, 0)',  # Transparent paper background
        font=dict(color='white'),  # White font color
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor="rgba(0, 0, 0, 0.8)",  # Semi-transparent black background for hover label
            font_size=14,
            font_family="Rockwell",
            font_color='white'  # White color for hover text
        ),
        yaxis=dict(
            autorange="reversed" if platform_name == "Lakuemas" else True,
            gridcolor='rgba(255, 255, 255, 0.2)',  # Light grid lines
            zerolinecolor='rgba(255, 255, 255, 0.2)',  # Light zero line
            tickcolor='white',  # White tick color
            tickfont=dict(color='white')  # White tick font color
        ),
        xaxis=dict(
            gridcolor='rgba(255, 255, 255, 0.2)',  # Light grid lines
            zerolinecolor='rgba(255, 255, 255, 0.2)',  # Light zero line
            tickcolor='white',  # White tick color
            tickfont=dict(color='white')  # White tick font color
        ),
    )

    # Custom hover template
    hover_template = '<b>Spread</b>: %{y:.3f}%<br>' + \
                      '<b>Buy</b>: %{customdata[0]}<br>' + \
                      '<b>Sell</b>: %{customdata[1]}'

    if platform_name == "Lakuemas":
        hover_template = '<b>Date</b>: %{x}<br>' + hover_template

    fig.update_traces(
        hovertemplate=hover_template,
        customdata=df_sorted[['Buy', 'Sell']].values
    )

    return fig



############ Get brankaslm latest data ############
url = 'https://www.brankaslm.com/antam/simulation'
# Use cloudscraper to bypass Cloudflare's anti-bot page
scraper = cloudscraper.create_scraper()
response = scraper.get(url).text

# Parse the HTML content with BeautifulSoup
soup = BeautifulSoup(response, 'html.parser')

# Use CSS selectors to extract the desired data
buy = soup.select_one('#content > div > div > div > div:nth-child(1) > div > div:nth-child(2) > div > table > tbody > tr:nth-child(1) > td:nth-child(2)').text
sell = soup.select_one('#content > div > div > div > div:nth-child(1) > div > div:nth-child(2) > div > table > tbody > tr:nth-child(2) > td:nth-child(2)').text
date_text = soup.select_one('#content > div > div > div > div:nth-child(1) > div > div:nth-child(2) > div > form > div > p').text

# Extract the date and time part from "Perubahan terakhir : 08-09-2024 06:48:26"
date_str = date_text.split(": ", 1)[1]
# Parse the extracted date string to a datetime object
date = datetime.strptime(date_str, '%d-%m-%Y %H:%M:%S')

# Get the latest data
latest_spread_df = insert_data(latest_spread_df, 'Brankaslm', buy, sell, date)



############ Get pegadaian latest data ############
interval_range = 4 * 365
url = 'https://agata.pegadaian.co.id/public/webcorp/konven/pegadaian-api/fluktuasi-harga-emas?time_interval=' + str(interval_range)
headers={'apikey':'c76d2050-f78a-43ea-a259-7d1b0a7a378f'}
response = requests.get(url, headers=headers)
data = json.loads(response.content)

# Get historical data
for idx, day in enumerate(data['data']['priceList']):
  buy = int(day['hargaJual']) * 100
  sell = int(day['hargaBeli']) * 100
  date = day['lastUpdate']
  pegadaian_df = insert_data(pegadaian_df, 'Pegadaian', buy, sell, str(date), True)

# Get the latest data
latest_spread_df = insert_latest_data(latest_spread_df, pegadaian_df)

# Get the plotting figure
pegadaian_fig = plot_gold_spread(pegadaian_df, 'Pegadaian')



############ Get indogold data ############
interval_range = 4 * 365
urls = ['https://www.indogold.id/ajax/chart_interval/GOLD/', 'https://www.indogold.id/ajax/chart_interval_jual/GOLD/']

# Get historical data
buy_prices = []
sell_prices = []
for idx, url in enumerate(urls):
  response = requests.post(url+str(interval_range))
  data = json.loads(response.content)
  for day in data[0]['data']:
    if idx == 0:
      buy_prices.append(day[1])
    else:
      sell_prices.append(day[1])

for idx, (buy, sell) in enumerate(zip(buy_prices, sell_prices)):
  date = format_datetime(datetime_jakarta - timedelta(days=interval_range-idx))
  indogold_df = insert_data(indogold_df, 'Indogold', buy, sell, date, True)

# Get the latest data
latest_spread_df = insert_latest_data(latest_spread_df, indogold_df)

# Get the plotting figure
indogold_fig = plot_gold_spread(indogold_df, 'Indogold')



############ Get lakuemas data ############
url = 'https://www.lakuemas.com/api/harga/change_graph'
body = {'length': '3mon'}
response = requests.post(url, data=body)
data = json.loads(response.content)

# Get historical data
for label, sell, buy in zip(data['data']['label'], data['data']['harga_beli'], data['data']['harga_jual']):
  date = datetime.strptime(label, '%d %b %Y - %H:%M')
  lakuemas_df = insert_data(lakuemas_df, 'Lakuemas', buy, sell, str(date), True)

# Get the latest data
latest_spread_df = insert_latest_data(latest_spread_df, lakuemas_df)

# Get the plotting figure
lakuemas_fig = plot_gold_spread(lakuemas_df, 'Lakuemas')



############ Get pluang data ############
interval_range = 4 * 365
url = 'https://api-pluang.pluang.com/api/v3/asset/gold/pricing?daysLimit=' + str(interval_range)
response = requests.get(url)
data = json.loads(response.content)

# Get historical data
for idx, day in enumerate(data['data']['history']):
  buy = day['sell']
  sell = day['buy']
  date = convert_to_jakarta_date(day['updated_at'])
  pluang_df = insert_data(pluang_df, 'Pluang', buy, sell , date, True)

# Get the latest data
latest_spread_df = insert_latest_data(latest_spread_df, pluang_df)

# Get the plotting figure
pluang_fig = plot_gold_spread(pluang_df, 'Pluang')



############ Get treasury data ############
url = 'https://api.treasury.id/api/v1/antigrvty/gold/rate'
rate_type = ['buying_rate', 'selling_rate']
sell_prices = []
buy_prices = []
dates = []

def fetch_tresury_data(start_date, end_date):
    for rt in rate_type:
      body = {'start_date': start_date, 'end_date': end_date, 'type': rt}
      response = requests.post(url, data=body)
      data = json.loads(response.content)
      for day in data['data']:
          if rt == 'buying_rate':
              buy_prices.append(day[rt])
              dates.append(day['date'])
          else:
              sell_prices.append(day[rt])


# Loop through the date range in 1-year increments
# This is necessary because the API returns incomplete data for periods longer than one year, skipping several days at a time.
current_start_date = datetime_jakarta - timedelta(days=4 * 365)
while current_start_date <= datetime_jakarta:
    current_end_date = min(current_start_date + timedelta(days=365), datetime_jakarta)
    fetch_tresury_data(current_start_date.strftime('%Y/%m/%d'), current_end_date.strftime('%Y/%m/%d'))
    current_start_date = current_end_date + timedelta(days=1)  # Move to the next day after the current end date

for date, buy, sell in zip(dates, buy_prices, sell_prices):
  date_object = datetime.strptime(date, '%d %b %Y')
  formatted_date = date_object.strftime('%Y-%m-%d %H:%M:%S')
  treasury_df = insert_data(treasury_df, 'Treasury', buy, sell, str(formatted_date), True)

# Fetch the latest data
# The previous API call does not provide the latest data
response = requests.post(url)
data = json.loads(response.content)['data']
treasury_df = insert_data(treasury_df, 'Treasury', data['buying_rate'], data['selling_rate'], str(data['updated_at']), True)

# Get the latest data
latest_spread_df = insert_latest_data(latest_spread_df, treasury_df)

# Get the plotting figure
treasury_fig = plot_gold_spread(treasury_df, 'Treasury')



############ Plot Combine Gold Spread ############
# Combine dataframes
combined_df = pd.concat([lakuemas_df, indogold_df, treasury_df, pluang_df, pegadaian_df])

# Sort the combined dataframe by date in ascending order
combined_df_sorted = combined_df.sort_values(by='Date')

# Create the chart
combined_fig = px.line(combined_df_sorted,
              x='Date',
              y='Spread',
              color='Platform',
              # title='Gold Spread Over Time Across Different Platforms',
              title = ' ',
              labels={'Date': 'Date', 'Spread': 'Spread (%)', 'Platform': 'Platform'},
              hover_data={'Buy': True, 'Sell': True, 'Platform': False})

# Customize the appearance and hover template
combined_fig.update_traces(line=dict(width=3),
                  hovertemplate='<br><b>Spread:</b> %{y:.3f}%<br>' +
                                '<b>Buy:</b> %{customdata[0]}<br>' +
                                '<b>Sell:</b> %{customdata[1]}')

combined_fig.update_layout(
    margin=dict(t=25, b=50),
    xaxis_title=None,
    yaxis_title=None,
    plot_bgcolor='rgba(0, 0, 0, 0)',  # Transparent background
    paper_bgcolor='rgba(0, 0, 0, 0)',  # Transparent paper background
    font=dict(color='#FFFFFF'),  # White font color
    hovermode='x unified',
    hoverlabel=dict(
        bgcolor="rgba(0, 0, 0, 0.8)",  # Semi-transparent black background for hover label
        font_size=14,
        font_family="Rockwell",
        font_color='#FFFFFF'  # White color for hover text
    ),
    yaxis=dict(
        gridcolor='rgba(255, 255, 255, 0.2)',  # Light grid lines
        zerolinecolor='rgba(255, 255, 255, 0.2)',  # Light zero line
        tickcolor='#FFFFFF',  # White tick color
        tickfont=dict(color='#FFFFFF')  # White tick font color
    ),
    xaxis=dict(
        gridcolor='rgba(255, 255, 255, 0.2)',  # Light grid lines
        zerolinecolor='rgba(255, 255, 255, 0.2)',  # Light zero line
        tickcolor='#FFFFFF',  # White tick color
        tickfont=dict(color='#FFFFFF')  # White tick font color
    ),
)



############ Plot Latest Gold Spread ############
# Sort the DataFrame by Spread
latest_spread_df = latest_spread_df.sort_values(by='Spread', ascending=False)

# Create the dumbbell chart
latest_fig = go.Figure()

# Add Buy points
latest_fig.add_trace(go.Scatter(
    x=latest_spread_df['Buy'], y=latest_spread_df['Platform'],
    mode='markers',
    marker=dict(size=20, color='gold'),
    customdata=latest_spread_df[['Date', 'Buy', 'Spread']],
    hovertemplate='<b>%{y}</b>'+
                '<br>Date: %{customdata[0]|%b %d, %Y, %H:%M}'+
                '<br>Buy Price: Rp%{customdata[1]:,.0f}'+
                '<br>Spread: %{customdata[2]:.3f}%<extra></extra>',
    name='Buy'
))

# Add Sell points
latest_fig.add_trace(go.Scatter(
    x=latest_spread_df['Sell'], y=latest_spread_df['Platform'],
    mode='markers',
    marker=dict(size=20, color='rgb(0, 104, 201)'),
    customdata=latest_spread_df[['Date', 'Sell', 'Spread']],
    hovertemplate='<b>%{y}</b>'+
                '<br>Date: %{customdata[0]|%b %d, %Y, %H:%M}'+
                '<br>Sell Price: Rp%{customdata[1]:,.0f}'+
                '<br>Spread: %{customdata[2]:.3f}%<extra></extra>',
    name='Sell'
))

# Add lines connecting the points and annotations for the spread text
for i in range(latest_spread_df.shape[0]):
    buy = latest_spread_df['Buy'][i]
    sell = latest_spread_df['Sell'][i]
    platform = latest_spread_df['Platform'][i]
    spread = f"{latest_spread_df['Spread'][i]:.3f}%"
    midpoint = (buy + sell) / 2
    
    latest_fig.add_shape(type='line',
                  x0=buy, y0=platform,
                  x1=sell, y1=platform,
                  line=dict(color='rgb(255, 43, 43)', width=3))
    
    latest_fig.add_annotation(
        x=midpoint, y=platform,
        text=spread,
        showarrow=False,
        font=dict(size=12, color='white'),
        align='center',
        yshift=10  # Adjust this value to move the text higher
    )

# Update layout for better aesthetics and add legend
latest_fig.update_layout(
    title=' ',
    margin=dict(t=25, b=0),
    xaxis_title=None,
    yaxis_title=None,
    plot_bgcolor='rgba(0, 0, 0, 0)',  # Transparent background
    paper_bgcolor='rgba(0, 0, 0, 0)',  # Transparent paper background
    font=dict(size=14, color='#FFFFFF'),  # White font color
    hoverlabel=dict(
        bgcolor="rgba(0, 0, 0, 0)",  # Semi-transparent black background for hover label
        font_family="Rockwell",
        font_color='#FFFFFF',  # White color for hover text
        font_size=14  # Adjust font size as needed
    ),
    legend=dict(
        title=None,
        itemsizing='constant',
        traceorder='normal'
    ),
    yaxis=dict(
        gridcolor='rgba(255, 255, 255, 0.2)',  # Light grid lines
        zerolinecolor='rgba(255, 255, 255, 0.2)',  # Light zero line
        tickcolor='#FFFFFF',  # White tick color
        tickfont=dict(color='#FFFFFF')  # White tick font color
    ),
    xaxis=dict(
        gridcolor='rgba(255, 255, 255, 0.2)',  # Light grid lines
        zerolinecolor='rgba(255, 255, 255, 0.2)',  # Light zero line
        tickcolor='#FFFFFF',  # White tick color
        tickfont=dict(color='#FFFFFF'),  # White tick font color
        tickprefix='Rp',  # Prefix for x-axis values
        tickformat=',.0f'  # Format for x-axis values
    )
)



############ Streamlit Layout ############
st.set_page_config(layout="wide", page_title="Emas Digital Spread")

style = """
<style>
.block-container
{
    padding-top: 1rem;
    margin-top: 1rem;
    padding-bottom: 1rem;
}
</style>
"""
st.markdown(style , unsafe_allow_html=True)


with st.container():
  col1, col2 = st.columns(2, vertical_alignment="bottom")

  with col1:
    with st.container():
      st.header("_Emas_ _Digital_ Spread Across Platforms", divider="gray", anchor=False, help=None)
      st.plotly_chart(latest_fig,  use_container_width=True)
      with st.popover("See Explanation", use_container_width=True):
        st.markdown("This chart shows the latest *Emas Digital* prices and spreads across platforms. Gold markers indicate the buying prices, while blue markers represent the selling prices. The lines between these markers show the spread, which is the difference between the buying and selling prices. All the data presented in the chart is collected through web scraping, utilizing APIs and specific data elements.")

  with col2:
      with st.container():
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Pegadaian", "Indogold", "Lakuemas", "Pluang", "Treasury"])
        with tab1:
          st.plotly_chart(pegadaian_fig,  use_container_width=True)
        with tab2:
            st.plotly_chart(indogold_fig,  use_container_width=True)
        with tab3:
            st.plotly_chart(lakuemas_fig,  use_container_width=True)
        with tab4:
            st.plotly_chart(pluang_fig,  use_container_width=True)
        with tab5:
            st.plotly_chart(treasury_fig,  use_container_width=True)

        with st.popover("See Explanation", use_container_width=True):
          st.markdown("This chart illustrates the spread history over the past four years for various platforms, with the exception of Lakuemas, which only provides data for the last three months. Each tab on the chart represents a different platform, showcasing their spread over time. All the data has been collected through web scraping, utilizing APIs.")

with st.container():
    st.plotly_chart(combined_fig,  use_container_width=True)

with st.container():
    footer = """
    <div style='text-align: center;'>
        <p>Crafted by <b>haikalzeo</b></p>
    </div>
    """
    st.markdown(footer, unsafe_allow_html=True)
