#!/usr/bin/python
#

import digdok_metashape as dd

mode = "db"

def get_project_queue():
  query = "SELECT COUNT(*) FROM new.view_process_location"
  count = int(dd.dbconnection(query, "select_one")[0])
  print(str(count) + " projects in queue.")
  return count

if __name__ == "__main__":
  count = get_project_queue()
  while count > 0:
  	print("Loading project.")
  	print()
  	dd.run(mode)
  	count = get_project_queue()
  else:
  	print("Project queue is empty. Exiting.")


