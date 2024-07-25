from django import forms
import pandas as pd

# Load the CSV file to get choices for the dropdowns
file_path = 'C:\\Users\\kyle\\OneDrive\\Documents\\Belson tech\\reidin-transaction-data.csv'
df = pd.read_csv(file_path)

# Get unique property types and communities from the CSV
property_types = df['Property Type'].unique()
communities = df['Community'].unique()

# Convert to tuples for form choices
PROPERTY_TYPE_CHOICES = [(ptype, ptype) for ptype in property_types]
COMMUNITY_CHOICES = [(comm, comm) for comm in communities]

class PropertyForm(forms.Form):
    property_type = forms.ChoiceField(label='Property type', choices=PROPERTY_TYPE_CHOICES, required=True)
    min_bedrooms = forms.IntegerField(label='Min bedrooms', required=False)
    max_bedrooms = forms.IntegerField(label='Max bedrooms', required=False)
    community = forms.ChoiceField(label='Community', choices=COMMUNITY_CHOICES, required=False)
    unit_size = forms.FloatField(label='Unit size', required=False)
    start_date = forms.DateField(label='Start date', required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    end_date = forms.DateField(label='End date', required=False, widget=forms.TextInput(attrs={'type': 'date'}))
