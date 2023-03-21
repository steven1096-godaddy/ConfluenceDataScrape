import json
import csv
from pprint import pprint


def create_csv_files(safe_parent_title, top_level_data):
    '''Creates the csv files for each top level page in the space'''
    filename = f"MSKB_CSVs/{safe_parent_title}.csv"
    csv_columns = ['id', 'title', 'url']
    try:
        with open(filename, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            writer.writerow(top_level_data)
    except IOError:
        print("I/O error")
    return True


def get_toplevel_pages(results):
    '''Returns a list of dicts the top level pages in the space'''
    top_level_pages = []
    top_level_with_children = []
    for result in results:
        parent_title = result.get("title")
        parent_id = result.get("id")
        parent_url = f'https://godaddy-corp.atlassian.net/wiki{result.get("_links")["webui"]}' # noqa
        safe_parent_title = parent_title.replace(" ", "")
        parent_children = result.get("children")
        top_level_data = {
            'id': parent_id,
            'title': parent_title,
            'url': parent_url,
            'safe_parent_title': safe_parent_title,
            'children': parent_children,
        }
        top_level_pages.append(top_level_data)
        top_level_with_children.append(top_level_data)
    return top_level_pages


def get_parent_children(top_level_page):
    '''loops through the passed in list
    Returns a list of dctionatiries of the parent page's children.
    '''
    parents_and_children = []
    parent = {
        'id': top_level_page.get('id'),
        'title': top_level_page.get('title'),
        'url': top_level_page.get('url'),
        'safe_parent_title': top_level_page.get('safe_parent_title')
    }
    parents_and_children.append({
        'parent': parent,
        'children': top_level_page.get('children', {}).get('page', {}).get('results', {}) # noqa
    })
    return parents_and_children


def add_to_csv(child, parent):
    '''Checks if there are children and if so,
    adds them to the proper excel sheet'''
    filename = f"MSKB_CSVs/{parent.get('safe_parent_title')}.csv"
    new_row = {
        'id': child['id'],
        'title': child['title'],
        'url': child.get('url'),
    }
    try:
        with open(filename, 'a') as csvfile:
            writer_object = csv.writer(csvfile)
            writer_object.writerow(new_row.values())
            csvfile.close()
    except IOError:
        print("I/O error")


def nested_next_level(child_article):
    '''Returns a list of the Next level pages that have child pages'''
    pages_with_children = []
    if len(child_article.get('children')['page']['results']) > 0:
        child_pages = child_article.get('children')['page']['results']
        for page in child_pages:
            pages_with_children.append(page)
    return pages_with_children


def scan_next_level(top_level_article):
    '''Accepts a top level page, appends the next level'''
    current_level_articles = []
    for page in top_level_article.get('children'):
        new_page = {
            'id': page['id'],
            'title': page['title'],
            'url': f"https://godaddy-corp.atlassian.net/wiki{page['_links']['webui']}", # noqa
        }
        current_level_articles.append(new_page)
    pages_with_children = []
    for page in top_level_article.get('children'):
        if len(page.get('children')['page']['results']) > 0:
            pages_with_children.append(page)
    return{
        'current_level_articles': current_level_articles,
        'pages_with_children': pages_with_children
    }


def main():
    jsonfile = 'articles.json'
    with open(jsonfile) as f:
        data = json.load(f)
    results = data['page']['results']
    top_level_pages = get_toplevel_pages(results)
    for item in top_level_pages:
        create_csv_files(
            item['safe_parent_title'],
            {
                'id': item['id'],
                'title': item['title'],
                'url': item['url'],
            }
        )

    # This section adds the first level of pages per top level page
    # It also extends a raw list of json objects
    # of sub pages that have children
    for top_page in top_level_pages:
        all_sub_pages = []
        pages_with_children = []

        children = get_parent_children(top_page)
        parent = {
            'id': top_page.get('id'),
            'title': top_page.get('title'),
            'url': top_page.get('url'),
            'safe_parent_title': top_page.get('safe_parent_title')
        }
        # This section loops though the first level and adds the first
        # level child pages to all_sub_pages[]
        # It also adds any pages with children to pages_with_children[]
        # to later parse through.
        for child in children:
            next_level = scan_next_level(child)
            for subpage in next_level.get('current_level_articles'):
                all_sub_pages.append(subpage)
            for page_with_child in next_level.get('pages_with_children'):
                pages_with_children.append(page_with_child)
        for items in all_sub_pages:
            add_to_csv(items, parent)

        all_sub_pages = []

        # This section loops through the pages_with_children[] and
        # extracts the next level child pages
        if len(pages_with_children) > 0:
            working_next_pages = pages_with_children
            pages_with_children = []
            for each_page in working_next_pages:
                children = each_page.get(
                    'children', {}).get('page', {}).get('results', {})
                for each_child in children:
                    # These are the new ones we need to append to the CSV list
                    all_sub_pages.append({
                        'id': each_child['id'],
                        'title': each_child['title'],
                        'url': f"https://godaddy-corp.atlassian.net/wiki{each_child.get('_links', {}).get('webui', {})}", # noqa
                    })
                    # These are the pages we appended that have sub children
                    next_level = nested_next_level(each_child)
                    for each_item in next_level:
                        pages_with_children.append(each_item)

        for items in all_sub_pages:
            add_to_csv(items, parent)

        all_sub_pages = []

        if len(pages_with_children) > 0:
            working_next_pages = pages_with_children
            pages_with_children = []
            for each_page in working_next_pages:
                children = each_page.get(
                            'children', {}).get('page', {}).get('results', {})
                for each_child in children:
                    all_sub_pages.append({
                        'id': each_child['id'],
                        'title': each_child['title'],
                        'url': f"https://godaddy-corp.atlassian.net/wiki{each_child.get('_links', {}).get('webui', {})}", # noqa
                    })
                    # These are the pages we appended that have sub children
                    next_level = nested_next_level(each_child)
                    for each_item in next_level:
                        pages_with_children.append(each_item)

        for items in all_sub_pages:
            add_to_csv(items, parent)



if __name__ == "__main__":
    main()
