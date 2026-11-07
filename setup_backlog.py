import os
import requests
import json

# ── Configuration ─────────────────────────────────────────────────────────────
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_USERNAME = "nihemelandu"
REPO_NAME = "causal-uplift-retail-email"
PROJECT_TITLE = "Master Product Backlog"

if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN environment variable not set. Run: set GITHUB_TOKEN=your_token_here")

HEADERS_GRAPHQL = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

# ── All 77 backlog items ──────────────────────────────────────────────────────
BACKLOG_ITEMS = [
    # Business Understanding
    {"name": "Define the eight Hillstrom questions that Sprint 1 answers", "type": "Business Understanding", "priority": 1, "status": "Done"},
    {"name": "Write business problem statement", "type": "Business Understanding", "priority": 2, "status": "Done"},
    {"name": "Write project vision statement — business and technical versions", "type": "Business Understanding", "priority": 3, "status": "Done"},

    # Data Understanding
    {"name": "Basic inspection — shape, dtypes, missing values, unit of analysis", "type": "Data Understanding", "priority": 4, "status": "Done"},
    {"name": "Treatment assignment mechanism — confirm randomization", "type": "Data Understanding", "priority": 5, "status": "Done"},
    {"name": "Outcome variable definition — visit, conversion, spend", "type": "Data Understanding", "priority": 6, "status": "Done"},
    {"name": "Duplicate row investigation", "type": "Data Understanding", "priority": 7, "status": "Done"},
    {"name": "Univariate analysis — distribution of each variable", "type": "Data Understanding", "priority": 8, "status": "Backlog"},
    {"name": "Bivariate analysis — outcome rates by each feature", "type": "Data Understanding", "priority": 9, "status": "Backlog"},
    {"name": "Class imbalance analysis — conversion rate", "type": "Data Understanding", "priority": 10, "status": "Backlog"},
    {"name": "Outlier inspection — history and recency", "type": "Data Understanding", "priority": 11, "status": "Backlog"},
    {"name": "Floor effect investigation — $29.99 minimum in history", "type": "Data Understanding", "priority": 12, "status": "Backlog"},

    # Data Preparation
    {"name": "Drop history_segment — redundant with history", "type": "Data Preparation", "priority": 13, "status": "Done"},
    {"name": "Create Mens Email vs No Email dataset", "type": "Data Preparation", "priority": 14, "status": "Done"},
    {"name": "Create Womens Email vs No Email dataset", "type": "Data Preparation", "priority": 15, "status": "Done"},
    {"name": "Define binary treatment variable for each dataset", "type": "Data Preparation", "priority": 16, "status": "Done"},

    # Modeling — Question 1
    {"name": "Compute ATE for Mens Email campaign across visit, conversion, spend", "type": "Modeling", "priority": 17, "status": "Done"},
    {"name": "Compute ATE for Womens Email campaign across visit, conversion, spend", "type": "Modeling", "priority": 18, "status": "Done"},
    {"name": "Two-sample T-test for statistical significance — Mens campaign", "type": "Modeling", "priority": 19, "status": "Done"},
    {"name": "Two-sample T-test for statistical significance — Womens campaign", "type": "Modeling", "priority": 20, "status": "Done"},

    # Modeling — Question 2
    {"name": "Compute incremental sales per customer for each campaign", "type": "Modeling", "priority": 21, "status": "Backlog"},

    # Modeling — Question 3
    {"name": "Build uplift model to identify best 10,000 customers to target", "type": "Modeling", "priority": 22, "status": "Backlog"},
    {"name": "Rank customers by individual treatment effect", "type": "Modeling", "priority": 23, "status": "Backlog"},
    {"name": "Identify top 10,000 customers for Mens campaign", "type": "Modeling", "priority": 24, "status": "Backlog"},
    {"name": "Identify top 10,000 customers for Womens campaign", "type": "Modeling", "priority": 25, "status": "Backlog"},

    # Modeling — Question 4
    {"name": "Identify 10,000 customers to suppress — negative treatment effect", "type": "Modeling", "priority": 26, "status": "Backlog"},
    {"name": "Characterize Sleeping Dogs — customers harmed by the campaign", "type": "Modeling", "priority": 27, "status": "Backlog"},

    # Modeling — Question 5
    {"name": "Analyse campaign performance by recency segment", "type": "Modeling", "priority": 28, "status": "Backlog"},
    {"name": "Analyse campaign performance by history segment", "type": "Modeling", "priority": 29, "status": "Backlog"},
    {"name": "Analyse campaign performance by channel", "type": "Modeling", "priority": 30, "status": "Backlog"},
    {"name": "Analyse campaign performance by zip code", "type": "Modeling", "priority": 31, "status": "Backlog"},
    {"name": "Analyse campaign performance by newbie status", "type": "Modeling", "priority": 32, "status": "Backlog"},
    {"name": "Analyse campaign performance by mens/womens purchase history", "type": "Modeling", "priority": 33, "status": "Backlog"},

    # Modeling — Question 6
    {"name": "Compare campaign performance across visit, conversion, and spend metrics", "type": "Modeling", "priority": 34, "status": "Done"},

    # Modeling — Question 7
    {"name": "Investigate anomalies and odd findings", "type": "Modeling", "priority": 35, "status": "Backlog"},
    {"name": "Document the $29.99 floor effect", "type": "Modeling", "priority": 36, "status": "Backlog"},
    {"name": "Document concentration of spend among small number of customers", "type": "Modeling", "priority": 37, "status": "Backlog"},

    # Modeling — Question 8
    {"name": "Define target audience for Mens campaign based on results", "type": "Modeling", "priority": 38, "status": "Backlog"},
    {"name": "Define target audience for Womens campaign based on results", "type": "Modeling", "priority": 39, "status": "Backlog"},

    # Evaluation
    {"name": "Cohens d effect size for Mens campaign across all metrics", "type": "Evaluation", "priority": 40, "status": "Done"},
    {"name": "Cohens d effect size for Womens campaign across all metrics", "type": "Evaluation", "priority": 41, "status": "Done"},
    {"name": "Qini curve for uplift model — Mens campaign", "type": "Evaluation", "priority": 42, "status": "Backlog"},
    {"name": "Qini curve for uplift model — Womens campaign", "type": "Evaluation", "priority": 43, "status": "Backlog"},
    {"name": "Accumulated ATE at targeting thresholds 10% through 100%", "type": "Evaluation", "priority": 44, "status": "Backlog"},

    # Deployment
    {"name": "Build Streamlit dashboard — Question 1", "type": "Deployment", "priority": 45, "status": "Done"},
    {"name": "Build Streamlit dashboard — Questions 2 through 8", "type": "Deployment", "priority": 46, "status": "Backlog"},
    {"name": "Deploy to Streamlit Community Cloud", "type": "Deployment", "priority": 47, "status": "Backlog"},
    {"name": "Write Sprint 1 README", "type": "Deployment", "priority": 48, "status": "Backlog"},

    # Future — Ruf and Handrich Replication
    {"name": "Introduce selection bias into Hillstrom data", "type": "Data Preparation", "priority": 49, "status": "Backlog"},
    {"name": "Propensity score matching — GBM estimation", "type": "Data Preparation", "priority": 50, "status": "Backlog"},
    {"name": "Validate covariate balance — SMD love plot before and after PSM", "type": "Data Preparation", "priority": 51, "status": "Backlog"},
    {"name": "S-learner — XGBoost and logistic regression", "type": "Modeling", "priority": 52, "status": "Backlog"},
    {"name": "T-learner — XGBoost and logistic regression", "type": "Modeling", "priority": 53, "status": "Backlog"},
    {"name": "X-learner — XGBoost and logistic regression", "type": "Modeling", "priority": 54, "status": "Backlog"},
    {"name": "R-learner — XGBoost and logistic regression", "type": "Modeling", "priority": 55, "status": "Backlog"},
    {"name": "Tailored uplift random forest — KL, ED, CHI criteria", "type": "Modeling", "priority": 56, "status": "Backlog"},
    {"name": "Churn propensity baseline — logistic regression, XGBoost, random forest", "type": "Modeling", "priority": 57, "status": "Backlog"},
    {"name": "Response propensity baseline — logistic regression, XGBoost, random forest", "type": "Modeling", "priority": 58, "status": "Backlog"},
    {"name": "Qini coefficient comparison — meta-learners vs uplift random forest", "type": "Evaluation", "priority": 59, "status": "Backlog"},
    {"name": "Accumulated ATE comparison — uplift vs propensity targeting", "type": "Evaluation", "priority": 60, "status": "Backlog"},
    {"name": "Computation time comparison", "type": "Evaluation", "priority": 61, "status": "Backlog"},

    # Future — Original Contribution
    {"name": "Build causal forest from scratch in Python", "type": "Modeling", "priority": 62, "status": "Backlog"},
    {"name": "Validate causal forest against EconML", "type": "Modeling", "priority": 63, "status": "Backlog"},
    {"name": "Causal forest via EconML — production benchmark", "type": "Modeling", "priority": 64, "status": "Backlog"},
    {"name": "Qini gap — winning meta-learner vs causal forest", "type": "Evaluation", "priority": 65, "status": "Backlog"},
    {"name": "Conversion lift at 30% targeting threshold", "type": "Evaluation", "priority": 66, "status": "Backlog"},

    # Data Quality — Deferred
    {"name": "Investigate $29.99 floor — minimum order value or data truncation", "type": "Data Understanding", "priority": 67, "status": "Backlog"},
    {"name": "Full univariate analysis — distribution of all variables", "type": "Data Understanding", "priority": 68, "status": "Backlog"},
    {"name": "Full bivariate analysis — feature vs outcome relationships", "type": "Data Understanding", "priority": 69, "status": "Backlog"},
    {"name": "Correlation matrix — multicollinearity detection", "type": "Data Understanding", "priority": 70, "status": "Backlog"},
    {"name": "VIF scores — feature redundancy", "type": "Data Understanding", "priority": 71, "status": "Backlog"},

    # Infrastructure
    {"name": "Set up GitHub Projects — Master Product Backlog", "type": "Infrastructure", "priority": 72, "status": "In Progress"},
    {"name": "Set up Streamlit Community Cloud deployment", "type": "Infrastructure", "priority": 73, "status": "Backlog"},
    {"name": "Write full project README", "type": "Infrastructure", "priority": 74, "status": "Backlog"},
    {"name": "Write data dictionary", "type": "Infrastructure", "priority": 75, "status": "Backlog"},
    {"name": "Write model documentation", "type": "Infrastructure", "priority": 76, "status": "Backlog"},
    {"name": "Learn Dash — daily incremental learning alongside Streamlit", "type": "Infrastructure", "priority": 77, "status": "Backlog"},
]


# ── Get repository ID ─────────────────────────────────────────────────────────
def get_repo_id():
    query = """
    query {
        repository(owner: "%s", name: "%s") {
            id
        }
    }
    """ % (GITHUB_USERNAME, REPO_NAME)

    response = requests.post(
        "https://api.github.com/graphql",
        headers=HEADERS_GRAPHQL,
        json={"query": query}
    )
    return response.json()["data"]["repository"]["id"]


# ── Get owner ID ──────────────────────────────────────────────────────────────
def get_owner_id():
    query = """
    query {
        user(login: "%s") {
            id
        }
    }
    """ % GITHUB_USERNAME

    response = requests.post(
        "https://api.github.com/graphql",
        headers=HEADERS_GRAPHQL,
        json={"query": query}
    )
    return response.json()["data"]["user"]["id"]


# ── Create GitHub Project ─────────────────────────────────────────────────────
def create_project(owner_id):
    query = """
    mutation {
        createProjectV2(input: {
            ownerId: "%s",
            title: "%s"
        }) {
            projectV2 {
                id
                number
            }
        }
    }
    """ % (owner_id, PROJECT_TITLE)

    response = requests.post(
        "https://api.github.com/graphql",
        headers=HEADERS_GRAPHQL,
        json={"query": query}
    )
    data = response.json()
    print("Create project response:")
    print(json.dumps(data, indent=2))
    project = data["data"]["createProjectV2"]["projectV2"]
    print(f"Created project: {PROJECT_TITLE} (ID: {project['id']}, Number: {project['number']})")
    return project["id"]


# ── Create custom field ───────────────────────────────────────────────────────
def create_field(project_id, field_name, field_type, options=None):
    if field_type == "SINGLE_SELECT" and options:
        options_str = ", ".join([
            f'{{name: "{o}", color: GRAY, description: ""}}'
            for o in options
        ])
        query = """
        mutation {
            createProjectV2Field(input: {
                projectId: "%s",
                dataType: SINGLE_SELECT,
                name: "%s",
                singleSelectOptions: [%s]
            }) {
                projectV2Field {
                    ... on ProjectV2SingleSelectField {
                        id
                        options {
                            id
                            name
                        }
                    }
                }
            }
        }
        """ % (project_id, field_name, options_str)

    elif field_type == "NUMBER":
        query = """
        mutation {
            createProjectV2Field(input: {
                projectId: "%s",
                dataType: NUMBER,
                name: "%s"
            }) {
                projectV2Field {
                    ... on ProjectV2Field {
                        id
                        name
                    }
                }
            }
        }
        """ % (project_id, field_name)

    else:
        query = """
        mutation {
            createProjectV2Field(input: {
                projectId: "%s",
                dataType: %s,
                name: "%s"
            }) {
                projectV2Field {
                    ... on ProjectV2Field {
                        id
                        name
                    }
                }
            }
        }
        """ % (project_id, field_type, field_name)

    response = requests.post(
        "https://api.github.com/graphql",
        headers=HEADERS_GRAPHQL,
        json={"query": query}
    )

    if response.status_code != 200:
        print(f"ERROR: HTTP {response.status_code} for field {field_name}")
        return None

    data = response.json()

    if "errors" in data:
        print(f"ERROR creating field {field_name}:")
        print(json.dumps(data["errors"], indent=2))
        return None

    print(f"Created field: {field_name}")
    print(json.dumps(data, indent=2))
    return data

# ── Add draft item to project ─────────────────────────────────────────────────
def add_draft_item(project_id, title):
    query = """
    mutation {
        addProjectV2DraftIssue(input: {
            projectId: "%s",
            title: "%s"
        }) {
            projectItem {
                id
            }
        }
    }
    """ % (project_id, title.replace('"', '\\"').replace("'", "\\'"))

    response = requests.post(
        "https://api.github.com/graphql",
        headers=HEADERS_GRAPHQL,
        json={"query": query}
    )
    data = response.json()
    return data["data"]["addProjectV2DraftIssue"]["projectItem"]["id"]


# ── Update item field ─────────────────────────────────────────────────────────
def update_item_field(project_id, item_id, field_id, value, field_type="text"):
    if field_type == "number":
        query = """
        mutation {
            updateProjectV2ItemFieldValue(input: {
                projectId: "%s",
                itemId: "%s",
                fieldId: "%s",
                value: {number: %s}
            }) {
                projectV2Item {
                    id
                }
            }
        }
        """ % (project_id, item_id, field_id, value)
    elif field_type == "single_select":
        query = """
        mutation {
            updateProjectV2ItemFieldValue(input: {
                projectId: "%s",
                itemId: "%s",
                fieldId: "%s",
                value: {singleSelectOptionId: "%s"}
            }) {
                projectV2Item {
                    id
                }
            }
        }
        """ % (project_id, item_id, field_id, value)

    response = requests.post(
        "https://api.github.com/graphql",
        headers=HEADERS_GRAPHQL,
        json={"query": query}
    )
    return response.json()


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("Setting up GitHub Project Master Product Backlog...")
    print(f"Repository: {GITHUB_USERNAME}/{REPO_NAME}")

    # Step 1 — Get owner ID
    print("\nStep 1: Getting owner ID...")
    owner_id = get_owner_id()
    print(f"Owner ID: {owner_id}")

    # Step 2 — Create project
    print("\nStep 2: Creating GitHub Project...")
    project_id = create_project(owner_id)

    # Step 3 — Create custom fields
    print("\nStep 3: Creating custom fields...")

    type_field = create_field(project_id, "Item Type", "SINGLE_SELECT", [
        "Business Understanding",
        "Data Understanding",
        "Data Preparation",
        "Modeling",
        "Evaluation",
        "Deployment",
        "Infrastructure",
        "Bug",
        "Research"
    ])
    print(f"Type field raw value: {type_field}")
    if type_field is None:
        print("ERROR: Item Type field creation failed.")
        return

    priority_field = create_field(project_id, "Priority/Rank", "NUMBER")
    print(f"Priority field raw value: {priority_field}")
    if priority_field is None:
        print("ERROR: Priority/Rank field creation failed.")
        return

    status_field = create_field(project_id, "Status", "SINGLE_SELECT", [
        "Backlog",
        "In Progress",
        "Done",
        "Deferred"
    ])
    print(f"Status field raw value: {status_field}")
    if status_field is None:
        print("ERROR: Status field creation failed.")
        return

    # Extract field IDs and option IDs safely
    print("\nExtracting field IDs...")

    type_field_data = type_field.get("data", {}).get("createProjectV2Field", {}).get("projectV2Field", {})
    type_field_id = type_field_data.get("id")
    type_options = {opt["name"]: opt["id"] for opt in type_field_data.get("options", [])}
    print(f"Type field ID: {type_field_id}")
    print(f"Type options: {type_options}")
    if not type_field_id or not type_options:
        print("ERROR: Type field ID or options could not be extracted.")
        return

    priority_field_data = priority_field.get("data", {}).get("createProjectV2Field", {}).get("projectV2Field", {})
    priority_field_id = priority_field_data.get("id")
    print(f"Priority field ID: {priority_field_id}")
    if not priority_field_id:
        print("ERROR: Priority field ID could not be extracted.")
        return

    status_field_data = status_field.get("data", {}).get("createProjectV2Field", {}).get("projectV2Field", {})
    status_field_id = status_field_data.get("id")
    status_options = {opt["name"]: opt["id"] for opt in status_field_data.get("options", [])}
    print(f"Status field ID: {status_field_id}")
    print(f"Status options: {status_options}")
    if not status_field_id or not status_options:
        print("ERROR: Status field ID or options could not be extracted.")
        return

    # Step 4 — Add all items
    print("\nStep 4: Adding all 77 backlog items...")
    for i, item in enumerate(BACKLOG_ITEMS, 1):
        print(f"  Adding item {i}/77: {item['name'][:60]}...")

        # Add draft issue
        item_id = add_draft_item(project_id, item["name"])

        # Update Item Type
        if item["type"] in type_options:
            update_item_field(project_id, item_id, type_field_id,
                              type_options[item["type"]], "single_select")

        # Update Priority/Rank
        update_item_field(project_id, item_id, priority_field_id,
                          item["priority"], "number")

        # Update Status
        if item["status"] in status_options:
            update_item_field(project_id, item_id, status_field_id,
                              status_options[item["status"]], "single_select")

    print(f"\n✓ Successfully populated Master Product Backlog with all 77 items.")
    print(f"View it at: https://github.com/{GITHUB_USERNAME}/{REPO_NAME}/projects")

if __name__ == "__main__":
    main()
