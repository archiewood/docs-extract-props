import re
import json
from pathlib import Path

def parse_frontmatter_and_content(markdown_content):
    # Regular expression to split content into frontmatter and main content
    blocks = re.split(r"---\n", markdown_content)
    
    parsed_components = []
    current_title = None
    
    for i in range(1, len(blocks)): 
        frontmatter = blocks[i]
        content = blocks[i+1] if i+1 < len(blocks) else ""
        
        # Extract title from frontmatter
        title_match = re.search(r"title:\s*['\"]?(?P<title>[^\"]+?)['\"]?$", frontmatter, re.MULTILINE)
        current_title = title_match.group("title").replace(" ", "") if title_match else None
        
        if current_title:
            # Split content by H1 headings
            sections = re.split(r'(?m)^#\s+(.+)$', content)
            
            if len(sections) > 1:
                # First section might be empty or have content before first H1
                if sections[0].strip():
                    parsed_components.append({
                        "title": current_title,
                        "content": sections[0]
                    })
                
                # Process remaining sections with their H1 headings
                for j in range(1, len(sections), 2):
                    heading = sections[j].strip().replace(" ","")
                    section_content = sections[j+1] if j+1 < len(sections) else ""
                    parsed_components.append({
                        "title": heading,
                        "content": section_content
                    })
            else:
                # No H1 headings found, use original title
                parsed_components.append({
                    "title": current_title,
                    "content": content
                })
    
    parsed_components.sort(key=lambda x: x["title"].lower())
    

    return parsed_components

def parse_proplistings(content):
    # Regular expression to match PropListing components
    pattern = re.compile(
        r"<PropListing\s+"
        r"name=(?P<name>[^\s\"]+|\"[^\"]+\")\s+"
        r"(?:description=(?P<description>[^\s\"]+|\"[^\"]+\")\s+)?"
        r"(?:required(?:=(?P<required>true|false))?\s+)?"
        r"(?:options=(?P<options>\{.*?\}|\[.*?\]|\"[^\"]*\"|[^\s>]+))?\s*"
        r"(?:defaultValue=(?P<defaultValue>[^\s>]+|\"[^\"]*\"))?\s*"
        r"(?:/>\s*|>(?P<content>.*?)</PropListing>)",
        re.DOTALL
    )

    props = []
    for match in pattern.finditer(content):
        name = match.group("name")
        description = match.group("description")
        required = match.group("required")
        required = required == "true" if required else "required" in match.group(0)
        options = match.group("options")
        default_value = match.group("defaultValue")
        content = match.group("content")

        # If no description attribute but content exists, use content as description
        if not description and content:
            description = content.strip()

        # Strip quotes from name, description
        if name:
            name = name.strip("\"")
        if description:
            description = description.strip("\"")

        # Parse options if available
        if options:
            options = options.strip()
            options = options.strip("\"")
            if options.startswith(("\"", "[", "{")):
                try:
                    options = eval(options)
                except:
                    pass

        # Parse default_value
        if default_value:
          if default_value == "-":
              default_value = None
          elif default_value in ["true", "false"]:
              default_value = default_value == "true"
          elif default_value.isdigit():
              default_value = int(default_value)
          elif default_value.replace(".", "", 1).isdigit():
              default_value = float(default_value)
          else:
              default_value = default_value.strip("\"")

        # Append prop to list
        props.append({
            "name": name,
            "description": description,
            "required": required,
            "type": "array" if isinstance(options, list) else "object" if isinstance(options, dict) else "string",
            "options": options,
            "defaultValue": default_value
        })

    return props

def process_markdown_file(file_path):
    excluded_components = [
        "QueryFunctions",
        "EvidenceDocs",
        "ThemesandLayouts",
        "Mixed-TypeCharts",
        "Chart`<Chart>`",
        "Line`<Line/>`",
        "Area`<Area/>`",
        "Bar`<Bar/>`",
        "Scatter`<Scatter/>`",
        "Bubble`<Bubble/>`",
        "Hist`<Hist/>`"
    ]

    with open(file_path, "r", encoding="utf-8") as file:
        markdown_content = file.read()

    components = parse_frontmatter_and_content(markdown_content)
    
    results = {}
    total_props = 0
    for component in components:
        title = component["title"]
        # Skip if component is in exclusion list
        if title in excluded_components:
            continue
            
        content = component["content"]
        props = parse_proplistings(content)
        proplen = len(props)
        if props:
            total_props += proplen
            print(f"{title}: {proplen}")
            results[title] = {"props": props}
    
    print(f"Total Props: {total_props}")
    return results

if __name__ == "__main__":
    try:
        # Specify the input markdown file
        input_file = "docs.txt"
        
        # Process the markdown file
        results = process_markdown_file(input_file)

        #print(json.dumps(results, indent=4))
        
        # Save the results to a JSON file
        output_file = ("props.json")
        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(results, file, indent=4)
        
        print(f"Props JSON generated and saved to {output_file}.")
    except Exception as e:
        print(f"An error occurred: {e}")