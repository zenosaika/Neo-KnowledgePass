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


def recommendation_result(request):
    context = {} # Initialize context dictionary
    backend_api_url = "http://localhost:8081/personalized_recommendation" # Define backend API URL

    if request.method == 'POST':
        # --- 1. Extract data from the POST request ---
        try:
            # Use getlist to handle multiple values for the same key
            courses = request.POST.getlist('courses')
            skills = request.POST.getlist('skills')

            # Use request.FILES.get to safely access the optional file
            resume_file = request.FILES.get('resume_file') # Name matches the HTML input name

            # Basic validation (optional but recommended)
            if not courses and not skills:
                 context['error'] = "Please select at least one course or skill."
                 return render(request, 'visualization/recommendation_result.html', context)

        except Exception as e:
            # Handle potential errors during data extraction
            print(f"Error extracting data from request: {e}")
            context['error'] = "There was an error processing your request input."
            return render(request, 'visualization/recommendation_result.html', context)

        # --- 2. Prepare data and files for the backend API call ---
        payload_data = {
            'courses': courses, # Send as lists
            'skills': skills
        }
        payload_files = {}
        if resume_file:
            # The key ('resume_file' here) MUST match what the backend API endpoint expects
            payload_files['resume_file'] = (resume_file.name, resume_file.read(), resume_file.content_type)

        # --- 3. Call the backend recommendation API ---
        try:
            print(f"Sending request to {backend_api_url}...")
            print(f"Data: {payload_data}")
            print(f"Files: {resume_file.name if resume_file else 'None'}")

            # Send request with data and potentially files (requests handles multipart/form-data)
            response = requests.post(backend_api_url, data=payload_data, files=payload_files, timeout=60) # Added timeout
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            recommendations = response.json()
            print("Received recommendations successfully.")

        # --- Handle potential errors during API call ---
        except requests.exceptions.Timeout:
            print("Error: Request to backend API timed out.")
            context['error'] = "The recommendation request took too long. Please try again later."
            return render(request, 'visualization/recommendation_result.html', context)
        except requests.exceptions.ConnectionError:
            print(f"Error: Could not connect to the backend API at {backend_api_url}.")
            context['error'] = "Could not connect to the recommendation service. Please ensure it's running."
            return render(request, 'visualization/recommendation_result.html', context)
        except requests.exceptions.RequestException as e:
            # Catch other requests errors (like HTTPError from raise_for_status)
            print(f"Error sending request to backend API: {e}")
            context['error'] = f"An error occurred while communicating with the recommendation service: {e}"
            # You might want to check response content here if available:
            # if e.response is not None: context['error'] += f" (Details: {e.response.text})"
            return render(request, 'visualization/recommendation_result.html', context)
        except (ValueError, json.JSONDecodeError):
            # Catch errors decoding the JSON response
            print("Error decoding JSON response from backend API.")
            context['error'] = "Received an invalid response from the recommendation service."
            return render(request, 'visualization/recommendation_result.html', context)
        except Exception as e:
             # Catch any other unexpected errors during API call phase
             print(f"An unexpected error occurred during API call: {e}")
             context['error'] = "An unexpected error occurred while fetching recommendations."
             return render(request, 'visualization/recommendation_result.html', context)


        # --- 4. Process the recommendations (Sankey data generation) ---
        try:
            # Check if recommendations were actually received
            if not recommendations or 'single_hop_sankey_df' not in recommendations or 'multi_hop_sankey_df' not in recommendations or 'ranked_jobs' not in recommendations:
                 print("Warning: Received incomplete data structure from backend API.")
                 context['warning'] = "Recommendation data received is incomplete. Visualization might be affected."
                 # Decide how to proceed - maybe return here or try to process what's available

            k = 3 # Number of top jobs to focus on for visualization
            sankey_datas = []

            # --- Single-hop Sankey Data ---
            if 'single_hop_sankey_df' in recommendations and recommendations['single_hop_sankey_df']:
                df2 = pd.DataFrame(recommendations['single_hop_sankey_df'])
                if not df2.empty and 'job' in df2.columns and 'data' in df2.columns:
                    grp = df2.groupby('job')
                    top_k_jobs = [v[0] for v in recommendations.get('ranked_jobs', [])[:k]]

                    S = set()
                    for job in top_k_jobs:
                        if job in grp.groups: # Check if job exists in the grouped data
                            g = grp.get_group(job)
                            # Ensure 'data' column contains iterable values (like lists/tuples)
                            valid_data = [tuple(v) for v in g.data.values if isinstance(v, (list, tuple)) and len(v) == 3]
                            s = set(valid_data)
                            S = S.union(s)
                    single_hop_sankey_data = list(S)
                    sankey_datas.append(json.dumps({'data': single_hop_sankey_data}))
                else:
                     print("Warning: Single-hop DataFrame is empty or missing required columns ('job', 'data').")
            else:
                print("Warning: No single-hop data found in recommendations.")


            # --- Multi-hop Sankey Data ---
            if 'multi_hop_sankey_df' in recommendations and recommendations['multi_hop_sankey_df']:
                df = pd.DataFrame(recommendations['multi_hop_sankey_df'])
                if not df.empty and all(col in df.columns for col in ['course', 'job', 'data']):
                    grp = df.groupby(['course', 'job'])
                    top_k_jobs = [v[0] for v in recommendations.get('ranked_jobs', [])[:k]]
                    all_input_nodes = courses + ['_SKILL'] # Use the *actual* courses from input

                    for node in all_input_nodes:
                        S = set()
                        for job in top_k_jobs:
                            if (node, job) in grp.groups: # Check if group exists
                                try:
                                    g = grp.get_group((node, job))
                                    # Ensure 'data' column contains iterable values
                                    valid_data = [tuple(v) for v in g.data.values if isinstance(v, (list, tuple)) and len(v) == 3]
                                    s = set(valid_data)
                                    S = S.union(s)
                                except KeyError:
                                    # Should not happen due to 'in grp.groups' check, but belt-and-suspenders
                                    pass

                        if S: # Only process if we found links for this course/skill
                            sankey_data_with_weights = list(S)
                            # Assuming data format is (src, dst, weight)
                            sankey_links = [(src, dst) for src, dst, _ in sankey_data_with_weights]

                            # Remove cycles (using your imported/defined function)
                            edges_to_remove = find_and_break_cycles(sankey_links)
                            acyclic_links = [edge for edge in sankey_links if edge not in edges_to_remove]
                            # Reconstruct with weight (using 1 for simplicity after cycle breaking)
                            final_sankey_data = [(src, dst, 1) for src, dst in acyclic_links]

                            if final_sankey_data: # Only append if data remains after cycle removal
                                sankey_datas.append(json.dumps({'data': final_sankey_data}))
                else:
                     print("Warning: Multi-hop DataFrame is empty or missing required columns ('course', 'job', 'data').")
            else:
                print("Warning: No multi-hop data found in recommendations.")

            # Add the generated sankey_datas to the context
            context['sankey_datas'] = sankey_datas
            # Add other potential results if needed by the template
            # context['ranked_jobs'] = recommendations.get('ranked_jobs', [])
            # context['summary'] = recommendations.get('summary', 'No summary available.')

            top_k_internships_data = []
            ranked_jobs = recommendations.get('ranked_jobs', [])
            for i, (job_title, score) in enumerate(ranked_jobs[:3]): # Get top 3
                # --- You'll need to fetch company info based on job_title ---
                company_name = "Censored Corp Inc." # Replace with actual company lookup logic
                # ---

                top_k_internships_data.append({
                    'rank': i + 1,
                    'title': job_title,
                    'company': company_name,
                    'score': f'{score*100:.0f}',
                })

            context['top_internships'] = top_k_internships_data

        except Exception as e:
            # Catch errors during data processing
             print(f"Error processing recommendation data: {e}")
             # Include traceback for debugging if possible in logs
             import traceback
             traceback.print_exc()
             context['error'] = "An error occurred while processing the recommendation results."
             # Still try to render, but with the error message
             return render(request, 'visualization/recommendation_result.html', context)

        # --- 5. Render the template with context ---
        return render(request, 'visualization/recommendation_result.html', context)

    else:
        # Handle GET requests (or other methods)
        # Option 1: Show a message
        context['message'] = "Please submit your profile via the form to get recommendations."
        # Option 2: Redirect to the form page (replace 'form_page_name' with your actual URL name)
        # from django.shortcuts import redirect
        # return redirect('form_page_name')
        return render(request, 'visualization/recommendation_result.html', context)