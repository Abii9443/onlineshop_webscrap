from flask import Flask, request, jsonify, render_template ,make_response
import numpy as np
import requests
from datetime import datetime
from datetime import date
import csv
import pandas as pd
import flask_excel as excel
import os
import re
from bs4 import BeautifulSoup
def flip_scrap(url):
    user_agent = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'}
    page = requests.get(url,headers=user_agent)
    soup=BeautifulSoup(page.content,"lxml")
    loc=soup.find_all('div',{'class':"_3pLy-c row"})
    return loc
def amazon_scrap(url):
    user_agent = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'}
    page = requests.get(url,headers=user_agent)
    soup=BeautifulSoup(page.content,"lxml")
    location=soup.find_all("div", {"class":"sg-col sg-col-4-of-12 sg-col-8-of-16 sg-col-12-of-20"})
    return location
def download(mobile_name,df):
    response =make_response(df.to_csv())
    response.headers["Content-Disposition"] = "attachment; filename="+mobile_name+ '.csv'
    return response
app = Flask(__name__)
@app.route('/')

def home():
    return render_template('index1.html')
@app.route('/price',methods=['GET'])
def price():
    return render_template('price.html')
    
@app.route('/single_pred',methods=['GET'])
def single_pred():
    return render_template('single_pred.html')
def flipkart_webscrape(mobile_name,scrap_pages):
    fliploc=[]
    for j in range(scrap_pages):
        URL = "https://www.flipkart.com/search?q="+mobile_name+"&page="
        flip_location = flip_scrap(f'{URL}{str(j)}')
        while(len(flip_location)==0):
            flip_location = flip_scrap(f'{URL}{str(j)}')
        fliploc.append(flip_location)
    flipkart=[]
    for flip_product in fliploc:
        for flip_product_src in flip_product:
            flip_specification=flip_product_src.find("li",{"class":"rgWa7D"}).text
            flip_mobile = flip_product_src.find('div',{"class":"_4rR01T"}).text
            flip_mobilename=flip_mobile.split('(')[0]
            if 'Power Bank ' in  flip_mobilename:
                continue
            try:  
                flip_mobcolor=flip_mobile.split('(')[1].split(',')[0]
                flip_ram=re.search(r'\d+',(flip_specification.split('|')[0])).group()
                flip_storage=re.search(r'\d+',(flip_specification.split('|')[1])).group()
            
            except(IndexError,AttributeError):
                continue
            try:
                flip_price=flip_product_src.find("div", {"class":"_3tbKJL"}).text.split("₹")[1].strip()
            except(IndexError,AttributeError):
                continue
            fill_flip=[]
            fill_flip.append(flip_mobilename.upper().strip())
            fill_flip.append(flip_mobcolor.upper().strip())
            fill_flip.append(flip_ram+'GB'.strip())
            fill_flip.append(flip_storage+'GB'.strip())
            fill_flip.append(int(flip_price.replace(',','').strip()))
            flipkart.append(fill_flip)
            df_flipkart = pd.DataFrame(flipkart)
            df_flipkart.columns = ["Mobile","Colour","Ram","Storage","Flipkart_Price"]
            df_flipkart.drop_duplicates(inplace=True)
            flipkart_datframe=df_flipkart
    return flipkart_datframe
@app.route('/scrap',methods =["GET", "POST"])
def scrap():
    if request.method == "POST":
        mobile_name = request.form.get("mobile_name")
        scrap_pages=request.form.get('scrap_pages')
        scrap_pages=int(scrap_pages)
        
    df_flipkart=flipkart_webscrape(mobile_name,scrap_pages)
    #print(df_flipkart)
    #myData = list(flipkart_datframe.values)
    return render_template('index1.html',column_names=df_flipkart.columns.values, row_data=list(df_flipkart.values.tolist()), zip=zip)
def amazon_webscrape(amazon_mobile_name,amazon_scrap_pages):
    loc=[]
    for j in range(amazon_scrap_pages):
        URL = "https://www.amazon.in/s?k=" + amazon_mobile_name.lower() + "&page="
        location = amazon_scrap(f'{URL}{str(j)}')
        while(len(location)==0):
            location = amazon_scrap(f'{URL}{str(j)}')
        loc.append(location)
    amazon=[]
    for product_name in loc:
        for product_src in product_name:
            
            specification_amazon=product_src.find("span", {"class":"a-size-medium a-color-base a-text-normal"}).text.split(")")[0]
            mobile_name=specification_amazon.split('(')[0].strip()
            if amazon_mobile_name.upper() not in mobile_name.upper() :
                continue
            try:
                ram_spec=re.search(r'\d+',specification_amazon.split('(')[1].split(',')[1]).group()
                storage_spec=re.search(r'\d+',specification_amazon.split('(')[1].split(',')[2].replace('Storage','ROM').strip()).group()
                mob_color=specification_amazon.split('(')[1].split(',')[0]
            except(IndexError,AttributeError):
                continue
            try:
                amazon_price = product_src.find("span", {"class":"a-offscreen"}).text.replace("₹","")
            except(AttributeError):
                continue
            amazon_mobile=[]
            amazon_mobile.append(mobile_name.upper().strip())
            amazon_mobile.append(mob_color.upper().strip())
            amazon_mobile.append(str(ram_spec)+'GB'.strip())
            amazon_mobile.append(str(storage_spec)+'GB'.strip())
            amazon_mobile.append(int(amazon_price.replace(',','').strip()))
            amazon.append(amazon_mobile)
            df_amazon = pd.DataFrame(amazon)
            df_amazon.columns = ["Mobile","Colour","Ram","Storage","Amazon_Price"]
            df_amazon.drop_duplicates(inplace=True)
            amazon_dataframe=df_amazon
    return amazon_dataframe
@app.route('/amazon',methods =["GET", "POST"])
def amazon():
    if request.method == "POST":
        amazon_mobile_name = request.form.get("amazon_mobile")
        amazon_scrap_pages=request.form.get('amazon_scrap_pages')
        amazon_scrap_pages=int(amazon_scrap_pages)
    df_amazon=amazon_webscrape(amazon_mobile_name,amazon_scrap_pages)
    return render_template('index1.html',column_names=df_amazon.columns.values, row_data=list(df_amazon.values.tolist()), zip=zip)
@app.route('/compare',methods =["GET", "POST"])
def compare():
    if request.method == "POST":
        online_mobile = request.form.get("mobile_name")
        online_scrap_pages=request.form.get('mobile_pages')
        df_amazon=amazon_webscrape(online_mobile,int(online_scrap_pages))
        df_flipkart=flipkart_webscrape(online_mobile,int(online_scrap_pages))
    result = pd.merge(df_amazon, df_flipkart,how='inner')
    result["Price_Difference"] = abs(result["Flipkart_Price"]-result["Amazon_Price"])
    #print(result)
    #result.to_csv("iqoo.csv", index=False)
    return render_template('price.html',column_names=result.columns.values, row_data=list(result.values.tolist()), zip=zip)
@app.route('/single',methods =["GET", "POST"])
def single():
    if request.method == "POST":
        single_mobile = request.form.get("single_mobile_name")
        single_color=request.form.get('single_mobile_color')
        single_ram=request.form.get('single_mobile_ram')+'GB'
        single_storage=request.form.get('single_mobile_storage')+'GB'
        # int_features = [str(x) for x in request.form.values()]
        df = pd.read_csv("vivo.csv")
        # final_features = [np.array(int_features)]
        # boolean_series = df['Mobile','Color','Ram','Storage'].isin(final_features)
        # filtered_df = df[boolean_series]
        df2 = df[(df['Mobile'] == single_mobile.upper()) & (df['Colour'] == single_color.upper()) & (df['Ram'] == single_ram) & (df['Storage'] == single_storage)]
        res_pric_flipcart = df2['Flipkart_Price'].to_string(index=False)
        res_pric_amazon = df2['Amazon_Price'].to_string(index=False)
        #return render_template('single_pred.html',result={res_pric_amazon})
        if(int(res_pric_flipcart) == int(res_pric_amazon )):
             return render_template('single_pred.html', text_result='You can prefer both Amazon or Flipkart', result='Amazon Price : '+(res_pric_amazon),result1='Flipkart Price :'+(res_pric_flipcart))
        if (int(res_pric_flipcart) > int(res_pric_amazon )):
            return render_template('single_pred.html', text_result='You can prefer  Amazon ', result='Amazon Price : '+(res_pric_amazon),result1='Flipkart Price :'+(res_pric_flipcart))
        else:
            return render_template('single_pred.html', text_result='You can prefer Flipkart ', result='Amazon Price : '+(res_pric_amazon),result1='Flipkart Price :'+(res_pric_flipcart))

    print(res_pric_flipcart)  
    print(res_pric_amazon)  

    #print(final_features)

        
        #print(data_xls)
if __name__ == "__main__":
    app.run(debug=True)