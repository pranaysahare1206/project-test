import streamlit as st
from fpdf import FPDF
import json
import os
import pandas as pd
from datetime import datetime
from PIL import Image

st.set_page_config(
    page_title="Shipping and Token Management App",
    page_icon="📦",
    layout="wide"
)

# Path for storing shipment data
data_file = 'shipments.json'

# Load existing shipments
if os.path.exists(data_file):
    with open(data_file, 'r') as f:
        shipments = json.load(f)
else:
    shipments = []


def save_shipments():
    with open(data_file, 'w') as f:
        json.dump(shipments, f, indent=4)


# PDF generation function
def generate_pdf(shipment, output_dir='pdfs'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Shipment ID: {shipment['tracking_id']}", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Admin Name: {shipment['admin_name']}", ln=True, align='L')
    pdf.cell(200, 10, txt=f"Request Platform: {shipment['request_platform']}", ln=True, align='L')
    pdf.cell(200, 10, txt=f"Company Name: {shipment['company_name']}", ln=True, align='L')
    pdf.cell(200, 10, txt="Users:", ln=True, align='L')
    for user, token in zip(shipment['users'], shipment['token_numbers']):
        pdf.cell(200, 10, txt=f"User: {user}, Token: {token}", ln=True, align='L')

    # Add a second page with user manual
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="User Manual", ln=True, align='C')
    pdf.multi_cell(0, 10,
                   txt="This is the user manual for the shipment process. Please ensure that all details are correctly filled out and verify shipment information before marking it as shipped.")

    # Use company name as the PDF file name
    company_name_safe = shipment['company_name'].replace(" ", "_").replace("/", "_")
    pdf_file_path = os.path.join(output_dir, f"{company_name_safe}.pdf")
    pdf.output(pdf_file_path)
    return pdf_file_path


def validate_shipment(tracking_id, admin_name, request_platform, company_name, users, token_numbers):
    if not tracking_id or not admin_name or not request_platform or not company_name:
        return "Please fill in all required fields."
    if any(not user or not token for user, token in zip(users, token_numbers)):
        return "All users and token numbers must be provided."
    return None


def main():
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        # Center the login content
        st.markdown(
            """
            <style>
            .centered {
                text-align: center;
                padding: 20px;
            }
            </style>
            <div class="centered">
                <h1>Token Shipping Management</h1>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Display the image centered
        # image = Image.open('login.jpg')
        #
        # st.image(image, caption='Login Image', use_column_width=False, width=400)


        st.write("\n")  # Add some space before the login form

        # Role selection and password input
        role = st.selectbox("Select Role", ["Token Team", "Shipping Team"])
        password = st.text_input("Enter Password", type="password")

        if st.button("Login"):
            if (role == "Token Team" and password == "54321") or (role == "Shipping Team" and password == "12345"):
                st.session_state['logged_in'] = True
                st.session_state['role'] = role
                st.success("Login successful!")
            else:
                st.error("Invalid role or password.")
    else:
        st.title("Shipping and Token Management App")

        if st.session_state['role'] == "Token Team":
            st.subheader("Token Team Dashboard")
            st.write("Create a New Shipment")

            # Enter common shipment details
            tracking_id = st.text_input("Tracking ID", key="tracking")
            admin_name = st.text_input("Admin Name", key="admin")

            request_platform = st.selectbox(
                "Request Platform",
                ["AA", "BB", "CC", "DD", "Other"]
            )
            if request_platform == "Other":
                request_platform = st.text_input("Specify Other Platform", key="other_platform")

            company_name = st.text_input("Company Name", key="company")

            # Enter number of users
            num_users = st.number_input("Number of Users", min_value=1, max_value=50, step=1)

            # Create lists to store details for each user
            users = []
            token_numbers = []

            st.write("Enter User Details")

            # Create columns for user data entry
            for i in range(num_users):
                st.write(f"User {i + 1}")
                cols = st.columns(2)  # 2 columns for each of the fields
                user = cols[0].text_input(f"User {i + 1} Name", key=f"user_{i}")
                token_number = cols[1].text_input(f"Token Number {i + 1}", key=f"token_{i}")

                # Add details to respective lists
                users.append(user)
                token_numbers.append(token_number)

            # Validate fields individually
            def validate_field(value, name):
                if not value or value.strip() == "":
                    st.warning(f"Please fill in the {name}.")
                    return False
                return True

            # Create the shipment
            if st.button("Create Shipment"):
                valid = True
                # Check individual fields
                if not validate_field(tracking_id, "Tracking ID"):
                    valid = False
                if not validate_field(admin_name, "Admin Name"):
                    valid = False
                if request_platform == "Other" and not validate_field(request_platform, "Other Platform"):
                    valid = False
                elif not validate_field(company_name, "Company Name"):
                    valid = False

                # Check if lists are correctly filled
                if any(not validate_field(user, f"User {i + 1} Name") for i, user in enumerate(users)):
                    valid = False
                if any(not validate_field(token, f"Token Number {i + 1}") for i, token in enumerate(token_numbers)):
                    valid = False

                if valid:
                    shipment = {
                        "tracking_id": tracking_id,
                        "admin_name": admin_name,
                        "request_platform": request_platform,
                        "company_name": company_name,
                        "users": users,
                        "token_numbers": token_numbers,
                        "status": "Pending",
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    shipments.append(shipment)
                    save_shipments()
                    st.success("Shipment Created Successfully!")
                    generate_pdf(shipment)
                else:
                    st.warning("Please correct the highlighted fields.")

            # Button to show/hide history dashboard
            if st.button("View History Dashboard"):
                st.subheader("Shipment History")

                # Convert shipments to DataFrame for easier handling
                df = pd.DataFrame(shipments)

                # Ensure 'date' field exists in DataFrame
                if 'date' not in df.columns:
                    df['date'] = pd.NaT  # Assign NaT if 'date' column is missing

                # Expand DataFrame for CSV export
                expanded_df = pd.DataFrame([
                    {
                        "tracking_id": row["tracking_id"],
                        "request_platform": row["request_platform"],
                        "company_name": row["company_name"],
                        "user": user,
                        "token_number": token,
                        "status": row["status"],
                        "date": row.get("date", pd.NaT),
                        "admin_name": row["admin_name"]
                    }
                    for row in shipments
                    for user, token in zip(row["users"], row["token_numbers"])
                ])

                def highlight_status(s):
                    if s == 'Cancelled':
                        return 'background-color: #E74054; color: black;'
                    elif s == 'Pending':
                        return 'background-color: #FFFF00; color: black;'
                    elif s == 'Shipped':
                        return 'background-color: #4DFFA0; color: black;'
                    else:
                        return ''

                # Apply the highlighting to only the 'status' column
                styled_df = expanded_df.style.applymap(highlight_status, subset=['status'])

                st.dataframe(styled_df, height=500, width=1800)



        elif st.session_state['role'] == "Shipping Team":
            st.subheader("Shipping Team Dashboard")

            st.write("View and Process Shipments")

            # Show pending shipments
            pending_shipments = [s for s in shipments if s['status'] == 'Pending']

            if not pending_shipments:
                st.write("🚫 No Shipments Available")
            else:
                for index, shipment in enumerate(pending_shipments):
                    shipment_key = f"{shipment['tracking_id']}_{shipment['users'][0]}"

                    # Initialize session state for the shipment if not already set
                    if shipment_key not in st.session_state:
                        st.session_state[shipment_key] = {"shipped_disabled": False, "cancel_disabled": False}

                    # Shipment Details arranged horizontally
                    details_col1, details_col2, details_col3 = st.columns([1, 1, 1])

                    with details_col1:
                        st.write(f"**Shipment ID:** {shipment['tracking_id']}")
                        st.write(f"**Company Name:** {shipment['company_name']}")

                    with details_col2:
                        st.write(f"**Users:** {', '.join(shipment['users'])}")

                    with details_col3:
                        st.write(f"**Token Numbers:** {', '.join(shipment['token_numbers'])}")

                    # Buttons for actions
                    col1, col2, col3 = st.columns([1, 1, 1])

                    with col1:
                        if st.button("Mark as Shipped",
                                     key=f"shipped_{shipment_key}",
                                     disabled=st.session_state[shipment_key]["shipped_disabled"]):
                            shipment['status'] = 'Shipped'
                            save_shipments()
                            st.success(f"Shipment {shipment['tracking_id']} marked as shipped!")
                            st.session_state[shipment_key]["shipped_disabled"] = True
                            st.session_state[shipment_key]["cancel_disabled"] = True

                    with col2:
                        if st.button("Cancel Shipment",
                                     key=f"cancel_{shipment_key}",
                                     disabled=st.session_state[shipment_key]["cancel_disabled"]):
                            shipment['status'] = 'Cancelled'
                            save_shipments()
                            st.warning(f"Shipment {shipment['tracking_id']} cancelled!")
                            st.session_state[shipment_key]["shipped_disabled"] = True
                            st.session_state[shipment_key]["cancel_disabled"] = True

                    with col3:
                        pdf_file_path = generate_pdf(shipment)
                        company_name = shipment['company_name'].replace(" ", "_")

                        with open(pdf_file_path, "rb") as pdf_file:
                            st.download_button(label="Download PDF",
                                               data=pdf_file,
                                               file_name=f"{company_name}.pdf",
                                               mime="application/pdf",
                                               key=f"download_{shipment_key}")

                    # Add a line separator between shipments
                    st.markdown("---")

            if st.button("View History Dashboard"):
                st.subheader("Shipment History")

                # Convert shipments to DataFrame for easier handling
                df = pd.DataFrame(shipments)

                # Ensure 'date' field exists in DataFrame
                if 'date' not in df.columns:
                    df['date'] = pd.NaT  # Assign NaT if 'date' column is missing

                # Expand DataFrame for CSV export
                expanded_df = pd.DataFrame([
                    {
                        "tracking_id": row["tracking_id"],
                        "request_platform": row["request_platform"],
                        "company_name": row["company_name"],
                        "user": user,
                        "token_number": token,
                        "status": row["status"],
                        "date": row.get("date", pd.NaT)

                    }
                    for row in shipments
                    for user, token in zip(row["users"], row["token_numbers"])
                ])

                # Display the DataFrame with adjusted size
                st.dataframe(expanded_df, height=500, width=1800)


if __name__ == '__main__':
    main()
