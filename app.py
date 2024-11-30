from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup
import pandas as pd

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <form action="/process" method="post">
        <label for="url">Enter the URL of the webpage:</label><br>
        <input type="text" id="url" name="url"><br><br>
        <input type="submit" value="Submit">
    </form>
    '''

@app.route('/process', methods=['POST'])
def process():
    url = request.form['url']
    result = process_exam_data(url)
    return render_template_string(result)

def process_exam_data(url):
    response = requests.get(url)
    if response.status_code != 200:
        return "Failed to retrieve the page. Please check the URL."
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Main info panel
    main_info = soup.find("div", class_="main-info-pnl")
    if main_info:
        main_info_html = str(main_info)
        candidate_name = main_info.find("td", string="Candidate Name").find_next_sibling("td").text.strip()
    else:
        main_info_html = "Main info panel not found."
        candidate_name = "unknown_candidate"
    
    # List of results
    results = []
    
    # All sections
    sections = soup.find_all("div", class_="section-cntnr")
    for section in sections:
        # Section label
        section_lbl = section.find("div", class_="section-lbl").find_all("span")[-1].text.strip()
        
        # Clean the section label by removing leading numbers
        section_lbl = ''.join(filter(lambda x: not x.isdigit(), section_lbl)).strip()
        
        # Count of total questions in a section
        questions = section.find_all("div", class_="question-pnl")
        total_questions = len(questions)
        
        answered = 0
        right = 0
        wrong = 0
        
        for question in questions:
            # Question was answered or not
            menu_tbl = question.find("table", class_="menu-tbl")
            status_row = menu_tbl.find("td", string="Status :")
            if status_row:
                status = status_row.find_next_sibling("td").text.strip()
                if status == "Answered":
                    answered += 1
                    
                    # Extract chosen option
                    chosen_row = menu_tbl.find("td", string="Chosen Option :")
                    chosen_option = chosen_row.find_next_sibling("td").text.strip()
                    
                    # Find the correct option
                    right_ans = question.find("td", class_="rightAns")
                    if right_ans:
                        right_option = right_ans.text.split(".")[0].strip()
                        
                        # Compare chosen and correct options
                        if chosen_option == right_option:
                            right += 1
                        else:
                            wrong += 1
        
        unattempted = total_questions - answered
        
        # Calculate total marks based on the row position
        if len(results) < 2:
            total_marks = right * 3
        else:
            total_marks = (right * 3) - wrong
        
        # Append results
        results.append({
            "Section Label": section_lbl,
            "Total Questions": total_questions,
            "Answered": answered,
            "Unattempted": unattempted,
            "Right": right,
            "Wrong": wrong,
            "Total Marks": total_marks
        })
    
    # Convert results to a DataFrame
    df = pd.DataFrame(results)
    
    # Convert the DataFrame to HTML
    table_html = df.to_html(index=False)
    
    # Combine the main info panel and the table
    combined_html = f"{main_info_html}<br>{table_html}"
    
    # Saving data to a text file with the candidate's name
    with open(f"{candidate_name}.txt", "w") as file:
        file.write(main_info_html)
        file.write("\n\n")
        file.write(df.to_string(index=False))
    
    return combined_html

if __name__ == '__main__':
    app.run(debug=True)
