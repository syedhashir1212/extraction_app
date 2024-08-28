import sys
import warnings
import streamlit as st
import os
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter
import pdfplumber
import sqlite3
from sqlite_module import setup_database, insert_data_to_db, display_data_from_db  # Ensure these are implemented
import re
import base64

warnings.filterwarnings('ignore')

# warnings.filterwarnings("ignore", message=".*st.experimental_get_query_params.*")
# st.set_option('deprecation.showPyplotGlobalUse', False)


# def display():
#     st.header("Admin Page")
#     st.write("This is the admin-specific page.")

def extract_table_data(page):
    # Attempt to extract data from the third table
    tables = page.extract_tables()
    
    if len(tables) >= 3:
        # Extract first column from the third table
        third_table = tables[2]
        columns = list(zip(*third_table))
        first_column = [cell.strip() for cell in columns[0] if cell and cell.strip()]
        combined_text = ' '.join(first_column)
        
        # Extract data between "EQUIPMENT I.D.NO" and "Technique Particle"
        pattern = r'I\.D\.NO(.*?)Technique'
        match = re.search(pattern, combined_text, re.DOTALL)
        if match:
            extracted_data = match.group(1).strip()
            # Remove newline characters
            cleaned_data = extracted_data.replace('\n', ' ')
            return cleaned_data

    # If the first approach didn't return data, try the fourth table
    if len(tables) >= 4:
        # Extract fourth table
        fourth_table = tables[3]
        columns = list(zip(*fourth_table))
        first_column = [cell.strip() for cell in columns[0] if cell and cell.strip()]
        combined_text = ' '.join(first_column)
        
        # Extract data between "I.D NO." and "Technique"
        pattern = r'I\.D\s?NO\. *([^.]*)Technique'
        match = re.search(pattern, combined_text, re.DOTALL)
        if match:
            extracted_data = match.group(1).strip()
            # Remove newline characters
            cleaned_data = extracted_data.replace('\n', ' ')
            return cleaned_data
    
    # If the above approaches didn't return data, try the first table
    if len(tables) >= 1:
        # Extract first table
        first_table = tables[0]
        columns = list(zip(*first_table))
        first_column = [cell.strip() for cell in columns[0] if cell and cell.strip()]
        combined_text = ' '.join(first_column)
        
        # Extract data between "I.D NO." and "Technique"
        pattern = r'I\.D NO\.(.*?)Technique'
        match = re.search(pattern, combined_text, re.DOTALL)
        if match:
            extracted_data = match.group(1).strip()
            # Remove newline characters
            cleaned_data = extracted_data.replace('\n', ' ')
            return cleaned_data
    
    return 'No table data extracted.'
        

# Regular expressions for extracting data   
def extract_magnetic_particle_data(text):
    return {
        'Work Order No': re.search(r'W\.O\. No\.\s*(\d+)', text).group(1) if re.search(r'W\.O\. No\.\s*(\d+)', text) else 'N/A',
        'File Name': re.search(r'(MAGNETIC PARTICLE INSPECTION)', text).group(1).strip() if re.search(r'(MAGNETIC PARTICLE INSPECTION)', text) else 'N/A',
        'Type/Description': re.search(r'Material / Item Type and Description\s*([^\n]*)', text).group(1).strip() if re.search(r'Material / Item Type and Description\s*([^\n]*)', text) else 'N/A',
        'Location': re.search(r'Location\s*(.*?)\s*Cert\. No\.', text).group(1).strip() if re.search(r'Location\s*(.*?)\s*Cert\. No\.', text) else 'N/A',        'Certificate No': re.search(r'Cert\. No\.\s*(\S+)', text).group(1) if re.search(r'Cert\. No\.\s*(\S+)', text) else 'N/A',
        'Part No' : re.search(r'(?:Part No\.?|PROJECT|Project:)\s*(.*?)(?=\n|$)', text).group(1).strip() if re.search(r'(?:Part No\.?|PROJECT|Project:)\s*(.*?)(?=\n|$)', text) else 'N/A',
        'Serial No.': re.search(r'(?:Material \/ Item serial No\.\s*)?(\S.*?)(?:\s+(?:Part No|Project|PROJECT)|\s*$)', text).group(1) if re.search(r'(?:Material \/ Item serial No\.\s*)?(\S.*?)(?:\s+(?:Part No|Project|PROJECT)|\s*$)', text) else 'N/A',
        'Inspection Date': re.search(r'Date of Inspection\.\s*([\d\-]+)', text).group(1).strip() if re.search(r'Date of Inspection\.\s*([\d\-]+)', text) else 'N/A',
        'Expire Date': re.search(r"Validity of Inspection:\s*(\d{1,2}[-/]\w{3}[-/]\d{4}|\d{1,2}[-/]\d{2}[-/]\d{4})", text).group(1).strip() if re.search(r"Validity of Inspection:\s*(\d{1,2}[-/]\w{3}[-/]\d{4}|\d{1,2}[-/]\d{2}[-/]\d{4})", text) else 'N/A',
        'Fit for use': re.search(r'Results\s*:\s*(.*?)\s*Recommendation', text).group(1).strip() if re.search(r'Results\s*:\s*(.*?)\s*Recommendation', text) else 'N/A',
        'Fit/Rejected': re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', text).group(1).strip() if re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', text) else 'N/A',
        'Remarks': re.search(r'Area of inspection:\s*(.*?)\s*Results', text).group(1).strip() if re.search(r'Area of inspection:\s*(.*?)\s*Results', text) else 'N/A',
        'Customer': re.search(r"(?:Customer|CUSTOMER\s*:)\s*(.*?)\s*Date of Work", text).group(1).strip() if re.search(r"(?:Customer|CUSTOMER\s*:)\s*(.*?)\s*Date of Work", text) else 'N/A',
    }
    pass

def extract_ultrasonic_wall_thickness_data(text):
    return {
        "Work Order No": re.search(r"Work Order No:\s*(\d+)", text).group(1).strip() if re.search(r"Work Order No:\s*(\d+)", text) else None,
        "File Name": re.search(r"(.*?)(?=\s*Customer)", text).group(1).strip() if re.search(r"(.*?)(?=\s*Customer)", text) else None,                "Type/Description": re.search(r"(?:Material /Item type & Description:|Matrial /Item type & Description:)\s*(.*)", text).group(1).strip() if re.search(r"(?:Material /Item type & Description:|Matrial /Item type & Description:)\s*(.*)", text) else None,
        "Location": re.search(r"Location:\s*(.*?)\s*(?:Sub Location:)", text).group(1).strip() if re.search(r"Location:\s*(.*?)\s*(?:Sub Location:)", text) else None,
        "Certificate No": re.search(r"(?:Cert\. No ?:|Certificate No:)\s*(.*)", text).group(1).strip() if re.search(r"(?:Cert\. No ?:|Certificate No:)\s*(.*)", text) else None,
        "Serial No.": re.search(r"(?:Matrial /Item Type serial No:|Material /Item Type serial No:)\s*(.*?)\s*(?:Item Location:)", text).group(1) if re.search(r"(?:Matrial /Item Type serial No:|Material /Item Type serial No:)\s*(.*?)\s*(?:Item Location:)", text) else None,
        "Part No": re.search (r"Item Location:\s*(.*)", text).group(1).strip() if re.search(r"Item Location:\s*(.*)",text) else None,
        "Inspection Date": find_inspection_date(text),
        "Expire Date": extract_due_date(text),
        "Remarks": re.search(r"Recommendation\s*/\s*Comments\s*:\s*(.*)", text).group(1).strip() if re.search(r"Recommendation\s*/\s*Comments\s*:\s*(.*)", text) else None,
        "Customer": re.search(r"Customer\s*[:]\s*(.*?)\s*(?:Certificate No:|Rig / Well No:)", text).group(1).strip() if re.search(r"Customer\s*[:]\s*(.*?)\s*(?:Certificate No:|Rig / Well No:)", text) else None,
        "Fit For Use": re.search(r'Fit For Use:(.+?)(?=Work Order No)', text).group(1).strip() if re.search(r'Fit For Use:(.+?)(?=Work Order No)', text) else None,
        "Fit/Rejected": re.search(r'Fit/Rejected:(.+?)(?=Fit For Use)', text).group(1).strip() if re.search(r'Fit/Rejected:(.+?)(?=Fit For Use)', text) else None,

    }
    pass

def extract_lifting_gear_data(text,page):
    return {
        "Work Order No": re.search(r'W\.?O\.?NO:\s*(\S+)', text).group(1) if re.search(r'W\.?O\.?NO:\s*(\S+)', text) else None,
        "File Name": re.search(r'(.*?)\s*/ LIFTING APPLIANCES', text).group(1).strip() if re.search(r'(.*?)\s*/ LIFTING APPLIANCES', text) else None,
        "Type/Description": re.search(r'(.*?)\s*Customer:', text).group(1).strip() if re.search(r'(.*?)\s*Customer:', text) else None,
        "Location": re.search(r"Location:\s*(.*?)\s*(?=Rig & Well Number|W.O.NO:)", text).group(1) if re.search(r"Location:\s*(.*?)\s*(?=Rig & Well Number|W.O.NO:)", text) else None,
        "Certificate No": re.search(r'Certificate No\s*:\s*(.*)', text).group(1) if re.search(r'Certificate No\s*:\s*(.*)', text) else None,
        "Serial No." : extract_table_data(page=page),
        # "Serial No.": re.search(r'"(.*?)"', text).group(1).strip() if re.search(r'"(.*?)"', text) else None,
        "Part No": re.search (r"Location Of Item:?\s*(.*)", text).group(1).strip() if re.search(r"Location Of Item:?\s*(.*)",text) else None,
        "Inspection Date": re.search(r"(\d{2}-\d{2}-\d{4})\s+Due Date:", text).group(1) if re.search(r"(\d{2}-\d{2}-\d{4})\s+Due Date:", text) else None,
        "Expire Date": re.search(r'Due Date:\s*(\S+)', text).group(1).strip() if re.search(r'Due Date:\s*(\S+)', text) else None,
        "Fit For Use": re.search(r'FIT FOR USE:\s*(\S+)', text).group(1).strip() if re.search(r'FIT FOR USE:\s*(\S+)', text) else None,
        "Fit/Rejected": re.search(r'Fit/Rejected:\s*(\S+)', text).group(1).strip() if re.search(r'Fit/Rejected:\s*(\S+)', text) else None,
        "Remarks": re.search(r'Results\s*:(.*?)\n(?:Recommendation|Comments|\n\n)', text).group(1).strip() if re.search(r'Results\s*:(.*?)\n(?:Recommendation|Comments|\n\n)', text) else None,
        "Customer": re.search(r'Customer:\s*(.*?)\s*Location Of Item', text).group(1) if re.search(r'Customer:\s*(.*?)\s*Location Of Item', text) else None
    }    

def extract_drill_collar_data(text):
    return {
        
        'Work Order No': re.search(r"WORK ORDER NUM\s+(\d+)", text).group(1) if re.search(r"WORK ORDER NUM\s+(\d+)", text) else 'N/A',
        'File Name': re.search(r"(.*)INSPECTION REPORT", text).group(1).strip() if re.search(r"(.*)INSPECTION REPORT", text) else 'N/A',
        'Type/Description': re.search(r"Type Of Inspection\s+(.+?)\s+CONNECTION Type", text).group(1).strip() if re.search(r"Type Of Inspection\s+(.+?)\s+CONNECTION Type", text) else 'N/A',
        'Location': re.search(r"Location\s+(.+?)\s+CONSUMABLE TRACEABILITY", text).group(1).strip() if re.search(r"Location\s+(.+?)\s+CONSUMABLE TRACEABILITY", text) else 'N/A',        'Certificate No': re.search(r'Cert\. No\.\s*(\S+)', text).group(1) if re.search(r'Cert\. No\.\s*(\S+)', text) else 'N/A',
        "Certificate No": re.search(r"Certificate No:\s*(.*)", text).group(1) if re.search(r"Certificate No:\s*(.*)", text) else None,
        'Serial No.': re.search(r'(.*?)\s*Part No\.', text).group(1) if re.search(r'(.*?)\s*Part No\.', text) else 'N/A',
        'Inspection Date': re.search(r"DATE OF WORK\s+(\d{2}-\d{2}-\d{4})\s+INSPECTION NUMBER", text).group(1).strip() if re.search(r"DATE OF WORK\s+(\d{2}-\d{2}-\d{4})\s+INSPECTION NUMBER", text) else 'N/A',
        'Expire Date': re.search(r"\b\d{2}-\d{2}-\d{4}\b", text).group(0).strip() if re.search(r"\b\d{2}-\d{2}-\d{4}\b", text) else 'N/A',
        'Fit for use': re.search(r'Results\s*:\s*(.*?)\s*Recommendation', text).group(1).strip() if re.search(r'Results\s*:\s*(.*?)\s*Recommendation', text) else 'N/A',
        'Fit/Rejected': re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', text).group(1).strip() if re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', text) else 'N/A',
        'Remarks': re.search(r'Area of inspection:\s*(.*?)\s*Results', text).group(1).strip() if re.search(r'Area of inspection:\s*(.*?)\s*Results', text) else 'N/A',
        'Customer': re.search(r"Customer\s+(.+?)\s+Location", text).group(1).strip() if re.search(r"Customer\s+(.+?)\s+Location", text) else 'N/A'
    }    

def extract_load_test_data(text):

    return {
        'Work Order No': re.search(r'W\.?O\.?NO:\s*(\S+)', text).group(1) if re.search(r'W\.?O\.?NO:\s*(\S+)', text) else 'N/A',
        'File Name': re.search(r'(?:CERTIFICATE OF LOAD/ PROOF|CERTIFICATE OF LOAD TEST/ PROOF)(.*)& THOROUGH EXAMINATION(.*)', text).group(1).strip() if re.search(r'(?:CERTIFICATE OF LOAD/ PROOF|CERTIFICATE OF LOAD TEST/ PROOF)(.*)& THOROUGH EXAMINATION(.*)', text) else 'N/A',
        'Type/Description': re.search(r"(.*?)(?=\s*Customer)", text).group(1).strip() if re.search(r"(.*?)(?=\s*Customer)", text) else 'N/A',
        'Location': re.search(r"Location:\s*(.*?)\s*Rig & Well", text).group(1).strip() if re.search(r"Location:\s*(.*?)\s*Rig & Well", text) else 'N/A',
        'Certificate No' : re.search(r"Certificate No\s*:\s*(\S+)", text).group(1).strip() if re.search(r"Certificate No\s*:\s*(\S+)", text) else 'N/A',
        "Part No": re.search (r"Item Location:\s*(.*)", text).group(1).strip() if re.search(r"Item Location:\s*(.*)",text) else None,
        'Serial No.': re.search(r"\bSPK\S*\b", text).group(0) if re.search(r"\bSPK\S*\b", text) else 'N/A',
        'Inspection Date': re.search(r"(?:Inspection Date|Inspected Date)\s*(?:\:)?\s*(\d{2}-\d{2}-\d{4})\s*Due Date", text).group(1).strip() if re.search(r"(?:Inspection Date|Inspected Date)\s*(?:\:)?\s*(\d{2}-\d{2}-\d{4})\s*Due Date", text) else 'N/A',
        'Expire Date': re.search(r"Due Date:\s*(.*)", text).group(1).strip() if re.search(r"Due Date:\s*(.*)", text) else 'N/A',
        'Fit for use': re.search(r'Results\s*:\s*(.*?)\s*Recommendation', text).group(1).strip() if re.search(r'Results\s*:\s*(.*?)\s*Recommendation', text) else 'N/A',
        'Fit/Rejected': re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', text).group(1).strip() if re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', text) else 'N/A',
        'Remarks': re.search(r"REMARKS\s*:\s*(.*)", text).group(1).strip() if re.search(r"REMARKS\s*:\s*(.*)", text) else 'N/A',
        "Customer": re.search(r'Customer:\s*(.*?)\s*Location', text).group(1).strip() if re.search(r'Customer:\s*(.*?)\s*Location', text) else None

    }

def find_inspection_date(text):
    # Try the first pattern
    match = re.search(r"Work Order No:\s*\d+\s*(?:\n.*?\s*(\d{2}-\d{2}-\d{4})|(?:Inspection Date:\s*(\d{2}-\d{2}-\d{4})))", text, re.DOTALL)
    if match:
        return match.group(1) if match.group(1) else match.group(2)
    
    # If no match, try the second pattern
    match = re.search(r"Inspection Date:\s*(\d{2}-\d{2}-\d{4})", text)
    return match.group(1) if match else None

def extract_due_date(text):
    # Print text for debugging purposes
    # print("Text for due date extraction:", text)

    # First pattern: tries to find a date before "Inspection Date"
    pattern1 = r"(\d{2}-\d{2}-\d{4})(?=\s*Inspection Date)"
    match1 = re.search(pattern1, text)
    
    if match1:
        print(f"Found due date before 'Inspection Date': {match1.group(1)}")
        return match1.group(1)
    
    # Second pattern: tries to find a date after "Due Date:"
    pattern2 = r"Due Date:\s*(\d{2}-\d{2}-\d{4})"
    match2 = re.search(pattern2, text)
    
    if match2:
        # print(f"Found due date after 'Due Date:': {match2.group(1)}")
        return match2.group(1)
    
    # If neither pattern matches, return None
    print("No due date found.")
    return None


def identify_and_extract_data(pdf_path):
    # print("Identifying and extracting data from", pdf_path)  # Debug line
    inspection_results = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            # print("Extracted text from page:", text)  # Debug line
            if text:
                if "MAGNETIC PARTICLE INSPECTION REPORT" in text:
                    data = extract_magnetic_particle_data(text)
                elif "ULTRASONIC WALL THICKNESS MEASURMENT RECORD SHEET" in text:
                    data = extract_ultrasonic_wall_thickness_data(text)
                elif "LIFTING GEAR / LIFTING APPLIANCES / LIFTING EQUIPMENT" in text:
                    data = extract_lifting_gear_data(text,page)
                elif "DRILL COLLAR INSPECTION REPORT" in text:
                    data = extract_drill_collar_data(text)
                elif "LOAD TEST" in text:
                    data = extract_load_test_data(text)
                else:
                    data = None
            else:
                data = None

            if data:
                # Skip the PDF if 'File Name' is None
                if data.get('File Name') is None:
                    # print("Skipping page due to missing File Name")  # Debug line
                    continue  # Skip to the next page

                # Process the File Name if it's not None
                data['File Name'] = ''.join([word[0].upper() for word in data['File Name'].split()])
                data['Customer'] = ''.join(word[0].upper() for word in data['Customer'] .split())
                inspection_results.append(data)

    return inspection_results

def save_pdf_pages(pdf_path, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    inspection_results = identify_and_extract_data(pdf_path)  # Extract once

    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        num_pages = len(reader.pages)

        for i, result in enumerate(inspection_results):
            if not all(key in result for key in ['Work Order No', 'File Name', 'Type/Description', 'Location', 'Certificate No', 'Customer']):
                continue
            
            # Process Type/Description
            type_description = result.get('Type/Description', 'N/A')
            if type_description is not None and isinstance(type_description, str):
                type_description = type_description[:50] if len(type_description) > 50 else type_description
            else:
                type_description = 'N/A'
            
            # Process Customer
            customer = result.get('Customer', 'N/A')
            if customer is not None and isinstance(customer, str):
                customer_words = customer.split()
                customer = " ".join(customer_words[:5])  # Limit to the first three words
            else:
                customer = 'N/A'

            # Debugging output
            print(f"Original Type/Description: {result.get('Type/Description', 'N/A')}")
            print(f"Processed Type/Description: {type_description}")
            print(f"Original Customer: {result.get('Customer', 'N/A')}")
            print(f"Processed Customer: {customer}")

            filename = f"{result['Work Order No']}_{result['File Name']}_{type_description}_{result['Location']}_{result['Certificate No']}_{result['Expire Date']}_{customer}.pdf"
            cleaned_filename = clean_filename(filename)

            writer = PdfWriter()
            writer.add_page(reader.pages[i])

            # Create customer folder
            customer_folder = os.path.join(output_folder, clean_filename(customer))
            if not os.path.exists(customer_folder):
                os.makedirs(customer_folder)

            output_path = os.path.join(customer_folder, cleaned_filename)
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)

            # Insert data to DB if not already present
            insert_data_to_db(result, output_path)

def clean_filename(filename):
    # Clean the filename by removing invalid characters and limiting the length
    cleaned_filename = re.sub(r'[\\/:"*?<>|,]+', '', filename)
    cleaned_filename = cleaned_filename.replace('\n', ' ')
    max_length = 255  # Maximum filename length (common limit)
    if len(cleaned_filename) > max_length:
        cleaned_filename = cleaned_filename[:max_length]
    return cleaned_filename

def generate_pdf_link(pdf_blob, filename):
    if pdf_blob is None:
        return '<span>No PDF available</span>'
    pdf_base64 = base64.b64encode(pdf_blob).decode('utf-8')
    return f'<a href="data:application/pdf;base64,{pdf_base64}" download="{filename}">Download PDF</a>'



def main_admin():
    setup_database()


    st.title("PDF Inspection Report Management")
    st.sidebar.title("Options")

    uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)  # Allow multiple files

    if uploaded_files:  # Check if any files are uploaded
        st.sidebar.header("Processing PDFs")
        output_folder = st.sidebar.text_input("Output Folder Name", "output_pages")

        for uploaded_file in uploaded_files:  # Process each uploaded file
            pdf_path = os.path.join(output_folder, uploaded_file.name)

            if not os.path.exists(output_folder):
                os.makedirs(output_folder)  # Ensure the output folder exists

            with open(pdf_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())  # Save the uploaded file

            st.sidebar.success(f"PDF {uploaded_file.name} successfully uploaded and saved.")

            save_pdf_pages(pdf_path, output_folder)  # Process the PDF file

        if st.sidebar.button("Show Extracted Data"):
            df = display_data_from_db()

            if 'pdf_blob' in df.columns:
                df['PDF Link'] = df.apply(lambda row: generate_pdf_link(row['pdf_blob'], f"{row['work_order_no']}_{row['file_name']}.pdf"), axis=1)
                df = df.drop(columns=['pdf_blob'])

            df.head(200)
            st.write(df.to_html(escape=False), unsafe_allow_html=True)

# def main():
#     # Example authentication logic
#     if 'logged_in' in st.session_state and st.session_state['logged_in']:
#         user_role = st.session_state.get('user_role')
        
#         # Show admin page if user is an admin
#         if user_role == 'admin':
#             display()
#         else:
#             st.write("You do not have access to this page.")
#     else:
#         st.write("Please log in to access the application.")



if __name__ == "__main__":
    main_admin()


    # display()