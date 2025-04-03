from django.shortcuts import render
import json
import requests
import pandas as pd

def find_and_break_cycles(edges):
    adj = {}
    for u, v in edges:
        adj.setdefault(u, []).append(v)

    visited = set()
    recursion_stack = set()
    cycle_edges = set()

    def detect_cycle(node, path):
        visited.add(node)
        recursion_stack.add(node)
        path.append(node)

        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                if detect_cycle(neighbor, path):
                    return True
            elif neighbor in recursion_stack:
                # Cycle detected! The edge (node, neighbor) is part of a cycle.
                # We'll mark it for removal.
                cycle_edges.add((node, neighbor))
                return True
        recursion_stack.remove(node)
        path.pop()
        return False

    all_nodes = set([u for u, v in edges] + [v for u, v in edges])
    for node in all_nodes:
        if node not in visited:
            detect_cycle(node, [])

    return cycle_edges


def learning_path(request):
    courses = ["CN310", "CN311", "CN351", "SF210", "SF211",
                "SF212", "SF220", "SF222", "SF230",] # all courses in Software Engineering at Thammasat University
    skills = [""] # no skills

    context = {} # Initialize context dictionary
    backend_api_url = "http://localhost:8081/personalized_recommendation" # Define backend API URL

    if request.method == 'POST':
        # Get the list of desired roles
        roles = request.POST.getlist('selected_roles')  # Use getlist for multiple values with the same name
        print("Roles selected:", roles)
        # Get the uploaded job description file (if any)
        job_description_file = request.FILES.get('job_description_file')

        # --- 2. Prepare data and files for the backend API call ---
        payload_data = {
            'courses': courses, # Send as lists
            'skills': skills
        }
        payload_files = {}

        # --- 3. Call the backend recommendation API ---
        try:
            # Send request with data and potentially files (requests handles multipart/form-data)
            response = requests.post(backend_api_url, data=payload_data, files=payload_files, timeout=60) # Added timeout
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            recommendations = response.json()
            print("Received recommendations successfully.")

        # --- Handle potential errors during API call ---
        except requests.exceptions.Timeout:
            print("Error: Request to backend API timed out.")
            context['error'] = "The recommendation request took too long. Please try again later."
            return render(request, 'learning_path/learning_path.html', context)
        except requests.exceptions.ConnectionError:
            print(f"Error: Could not connect to the backend API at {backend_api_url}.")
            context['error'] = "Could not connect to the recommendation service. Please ensure it's running."
            return render(request, 'learning_path/learning_path.html', context)
        except requests.exceptions.RequestException as e:
            # Catch other requests errors (like HTTPError from raise_for_status)
            print(f"Error sending request to backend API: {e}")
            context['error'] = f"An error occurred while communicating with the recommendation service: {e}"
            # You might want to check response content here if available:
            # if e.response is not None: context['error'] += f" (Details: {e.response.text})"
            return render(request, 'learning_path/learning_path.html', context)
        except (ValueError, json.JSONDecodeError):
            # Catch errors decoding the JSON response
            print("Error decoding JSON response from backend API.")
            context['error'] = "Received an invalid response from the recommendation service."
            return render(request, 'learning_path/learning_path.html', context)
        except Exception as e:
             # Catch any other unexpected errors during API call phase
             print(f"An unexpected error occurred during API call: {e}")
             context['error'] = "An unexpected error occurred while fetching recommendations."
             return render(request, 'visualization/recommendation_result.html', context)

        # print("Recommendations received:", recommendations)

        job_requirements = {}
        student_skills = {}
        skill_details = {}

        for role in roles:
            job_fulfillment = recommendations['job_fulfillment'][role]

            job_requirements[role] = {
                'name': role,
                'skills': list(job_fulfillment.keys())
            }

            for k, v in job_fulfillment.items():
                student_skills[k] = True if v else False
                skill_details[k] = {'name': k}

        skill_course = {}
        for k, s in recommendations['skill_course_dict'].items():
            skill_course[k] = []
            for course in s:
                skill_course[k].append({'id': course, 'name': course, 'university': 'Thammasat University'})


        context = {
            'job_requirements_json': json.dumps(job_requirements),
            'student_skills_json': json.dumps(student_skills),
            'skill_details_json': json.dumps(skill_details),
            'skill_course_json': json.dumps(skill_course),
        }

        # --- 5. Render the template with context ---
        return render(request, 'learning_path/learning_path.html', context)

    else:
        # Handle GET requests (or other methods)
        # Option 1: Show a message
        context['message'] = "Please submit your profile via the form to get recommendations."
        # Option 2: Redirect to the form page (replace 'form_page_name' with your actual URL name)
        # from django.shortcuts import redirect
        # return redirect('form_page_name')
        return render(request, 'learning_path/learning_path.html', context)