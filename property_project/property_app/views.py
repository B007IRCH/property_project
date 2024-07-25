# views.py

from django.shortcuts import render
from django.http import JsonResponse
from .forms import PropertyForm
import pandas as pd
import os
import json
from django.conf import settings

# Load the CSV file
file_path = 'C:\\Users\\kyle\\OneDrive\\Documents\\Belson tech\\reidin-transaction-data.csv'
df = pd.read_csv(file_path)

# Convert relevant columns to numeric values
df['Size (Sqf)'] = df['Size (Sqf)'].str.replace(',', '').astype(float)
df['Amount (AED)'] = df['Amount (AED)'].str.replace(',', '').astype(float)
df['Bedrooms'] = df['Bedrooms'].str.split().str[0]
df = df.dropna(subset=['Bedrooms'])
df = df[df['Bedrooms'].str.isnumeric()]
df['Bedrooms'] = df['Bedrooms'].astype(int)
df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
if 'Unit' not in df.columns:
    df['Unit'] = ""

def filter_properties(df, property_type, community=None, unit_size=None, start_date=None, end_date=None):
    filtered_df = df[df['Property Type'] == property_type]
    if community:
        filtered_df = filtered_df[filtered_df['Community'] == community]
    if unit_size:
        unit_size_range = (unit_size * 0.8, unit_size * 1.2)
        filtered_df = filtered_df[(filtered_df['Size (Sqf)'] >= unit_size_range[0]) &
                                  (filtered_df['Size (Sqf)'] <= unit_size_range[1])]
    if start_date:
        filtered_df = filtered_df[filtered_df['Date'] >= pd.to_datetime(start_date)]
    if end_date:
        filtered_df = filtered_df[filtered_df['Date'] <= pd.to_datetime(end_date)]
    return filtered_df

def calculate_similarity(row, target_unit_size, target_bedrooms):
    size_diff = abs(row['Size (Sqf)'] - target_unit_size) if target_unit_size else 0
    bedroom_diff = abs(row['Bedrooms'] - target_bedrooms) if target_bedrooms else 0
    return size_diff + bedroom_diff * 100

def calculate_adjusted_sale_price(row, subject_size, price_per_sqft):
    adjustment_for_size = (subject_size - row['Size (Sqf)']) * price_per_sqft
    adjusted_price = row['Amount (AED)'] + adjustment_for_size
    return adjusted_price

def calculate_average_adjusted_price(properties, subject_size):
    total_adjusted_price = 0
    for prop in properties:
        total_adjusted_price += calculate_adjusted_sale_price(prop, subject_size, prop['price_per_sqft'])
    return total_adjusted_price / len(properties) if properties else None

def property_view(request):
    try:
        if request.method == 'POST':
            form = PropertyForm(request.POST)
            if form.is_valid():
                property_type = form.cleaned_data['property_type']
                min_bedrooms = form.cleaned_data.get('min_bedrooms')
                max_bedrooms = form.cleaned_data.get('max_bedrooms')
                community = form.cleaned_data.get('community')
                unit_size = form.cleaned_data['unit_size']
                start_date = form.cleaned_data['start_date']
                end_date = form.cleaned_data['end_date']

                filtered_properties = filter_properties(df, property_type, community, unit_size, start_date, end_date)

                selected_properties = json.loads(request.POST.get('selected_properties', '[]'))

                if selected_properties:
                    price_per_sqft = df['Amount (AED)'].mean() / df['Size (Sqf)'].mean()
                    for selected_property in selected_properties:
                        selected_property['price_per_sqft'] = price_per_sqft
                        selected_property['Adjusted Sale Price'] = calculate_adjusted_sale_price(
                            selected_property, unit_size, price_per_sqft)

                    average_adjusted_price = calculate_average_adjusted_price(selected_properties, unit_size)
                    average_adjusted_price = f"{average_adjusted_price:.2f}" if average_adjusted_price else None
                else:
                    average_adjusted_price = None

                if filtered_properties.empty:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'error': 'No properties found matching the criteria.'}, status=400)
                    else:
                        return render(request, 'property_app/property_form.html', {'form': form, 'no_results': True})
                else:
                    filtered_properties['Similarity'] = filtered_properties.apply(
                        lambda row: calculate_similarity(row, unit_size, min_bedrooms), axis=1)
                    sorted_properties = filtered_properties.sort_values(by='Similarity')

                    total_similar = len(sorted_properties)

                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        try:
                            cleaned_data = sorted_properties.head(50).fillna("").to_dict(orient='records')
                            cleaned_data = [
                                {
                                    'property': d.get('Property', ''),
                                    'amountAed': d.get('Amount (AED)', ''),
                                    'sizeSqf': d.get('Size (Sqf)', ''),
                                    'bedrooms': d.get('Bedrooms', ''),
                                    'community': d.get('Community', ''),
                                    'unit': d.get('Unit', ''),
                                    'date': d.get('Date', ''),
                                    'subtype': d.get('Subtype', ''),
                                    'transactionType': d.get('Transaction Type', ''),
                                    'developer': d.get('Developer', '')
                                } for d in cleaned_data
                            ]
                            response = JsonResponse({
                                'properties': cleaned_data,
                                'totalSimilar': total_similar,
                                'averageAdjustedPrice': average_adjusted_price
                            })
                            response['Content-Type'] = 'application/json'
                            return response
                        except Exception as e:
                            return JsonResponse({'error': str(e)}, status=500)

                    return render(request, 'property_app/property_form.html', {
                        'form': form,
                        'properties': [
                            {
                                'property': d.get('Property', ''),
                                'amountAed': d.get('Amount (AED)', ''),
                                'sizeSqf': d.get('Size (Sqf)', ''),
                                'bedrooms': d.get('Bedrooms', ''),
                                'community': d.get('Community', ''),
                                'unit': d.get('Unit', ''),
                                'date': d.get('Date', ''),
                                'subtype': d.get('Subtype', ''),
                                'transactionType': d.get('Transaction Type', ''),
                                'developer': d.get('Developer', '')
                            } for d in sorted_properties.head(50).fillna("").to_dict(orient='records')
                        ],
                        'total_similar': total_similar,
                        'average_adjusted_price': average_adjusted_price
                    })
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': 'Invalid form data.'}, status=400)
                else:
                    return render(request, 'property_app/property_form.html', {'form': form})
        else:
            form = PropertyForm()
            return render(request, 'property_app/property_form.html', {'form': form})
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=500)
        else:
            return render(request, 'property_app/property_form.html', {'form': PropertyForm(), 'error': str(e)})
