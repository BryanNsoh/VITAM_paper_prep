import requests
import os

def download_pdf(url, output_path):
    # Send a GET request to the URL
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Get the content type from the headers
        content_type = response.headers.get('Content-Type', '').lower()
        
        # Check if the content is a PDF
        if 'application/pdf' in content_type:
            # Write the content to a file
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"PDF downloaded successfully: {output_path}")
        else:
            print("The URL does not point to a PDF file.")
    else:
        print(f"Failed to download. Status code: {response.status_code}")

# Example usage
url = "https://www.jstage.jst.go.jp/article/jnsv/66/Supplement/66_S18/_pdf"
output_path = os.path.join(os.getcwd(), "downloaded_paper.pdf")

download_pdf(url, output_path)