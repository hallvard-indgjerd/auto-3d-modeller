#!/usr/bin/python
#
import Metashape
import digdok_metashape as dd

mode = "db"

def get_project_queue():
  query = "SELECT COUNT(*) FROM new.view_process_location"
  count = int(dd.dbconnection(query, "select_one")[0])
  print(str(count) + " projects in queue.")
  return count

if __name__ == "__main__":
  if mode == "db":
    count = get_project_queue()
    while count > 0:
      print("Loading project.")
      print()
      try:
        uuid = dd.run(mode)
      except Exception as e:
        # Set status failed
        print()
        print("!!!!! Exception !!!!!")
        print(e)
        print()
        dd.update_status(uuid, "status", "failed")
      else:
        # Set status done
        dd.update_status(uuid, "status", "done")
      count = get_project_queue()
    else:
      print("Project queue is empty. Exiting.")
  else:
    dd.run(mode)


