"""
You will need to add your authorization token in the code.
Here is how you do it.
1) In terminal run the following command
curl -i -u <your_username> -d '{"scopes": ["repo", "user"], "note": "OpenSciences"}' https://api.github.com/authorizations
2) Enter ur password on prompt. You will get a JSON response. 
In that response there will be a key called "token" . 
Copy the value for that key and paste it on line marked "token" in the attached source code. 
3) Run the python file. 
     python gitable.py
"""

import urllib.request, urllib.error, urllib.parse
import json, csv
import re, datetime
import sys, random, os


#global variables

token = os.environ['GITHUB_KEY']
#token = "" #set your token here 

class L():
  "Anonymous container"
  def __init__(i,**fields) : 
    i.override(fields)
  def override(i,d): i.__dict__.update(d); return i
  def __repr__(i):
    d = i.__dict__
    name = i.__class__.__name__
    return name+'{'+' '.join([':%s %s' % (k,pretty(d[k])) 
                     for k in i.show()])+ '}'
  def show(i):
    lst = [str(k)+" : "+str(v) for k,v in i.__dict__.items() if v != None]
    return ',\t'.join(map(str,lst))

def secs(d0):
  d     = datetime.datetime(*list(map(int, re.split('[^\d]', d0)[:-1])))
  epoch = datetime.datetime.utcfromtimestamp(0)
  delta = d - epoch
  return delta.total_seconds()
 
def dump1(u,issues, mapping):
  
  request = urllib.request.Request(u, headers={"Authorization" : "token "+token})
  v = urllib.request.urlopen(request).read()
  w = json.loads(v.decode())
  if not w: 
    return False
  
  random.shuffle(w)
  
  for event in w:
    if not event.get('label'):
      # we don't want any issue with no label
      # cannot derive any useful insight from it
      # as we do not have the title/content of the issue
      continue

    issue_id = event['issue']['number']
    #created_at = secs(event['created_at'])
    created_at = event['created_at']
    action = event['event']
    label_name = event['label']['name']
    
    milestone = event['issue']['milestone']
    if milestone != None : 
      milestone = milestone['title']
    assignea = event['issue']['assignee']
    assignee = None
    if assignea != None:
      assignee = assignea['login']
    comments = event['issue']['comments']
    
    issuecreated_at=secs(event['issue']['created_at'])
    issueclosed_at=event['issue']['closed_at']
    if not issueclosed_at:
      issueclosed_at = 0
      duration= issuecreated_at 
    else: 
      duration= secs(issueclosed_at)-issuecreated_at

    user = event['actor']['login']
    if not mapping.get(user):
      mapping[user] = "user{}".format(len(mapping)+1)
    user = mapping[user]

    eventObj = L(when=created_at,
           action = action,
           what = label_name,
           user = user,
           milestone = milestone,
           assignee=assignee,
           comments=comments,
           issuecreated_at=issuecreated_at,   
           issueclosed_at=issueclosed_at,
           duration=duration)
    
    #issueObj = L(created=created_at)

    if not issues.get(issue_id): 
      issues[issue_id] = []
    issues[issue_id].append(eventObj)
  
  for issue,events in issues.items():
    events.sort(key=lambda event: event.when)

  return True

def dump(u,issues, mapping):
  try:
    return dump1(u, issues, mapping)
  except Exception as e: 
    print(e)
    print("Contact TA")
    return False

def extractGroupCommentData(url,comments,token)
  comment_data ={}
  request = urllib.request.Request(url,headers={"Authorization" : "token "+token})
  v = urllib.request.urlopen(request).read()
  j = json.loads(v.decode())
  if not j:
    return False

  for comment in j:
    user = comment['user']['login']
    identifier = comment['id']
    issueid = int((comment['issue_url'].split('/'))[-1])
    comment_text = comment['body']
    created_at = secs(comment['created_at'])
    updated_at = secs(comment['updated_at'])
    commentObj = L(ident = identifier,
                issue = issueid, 
                user = user,
                text = comment_text,
                created_at = created_at,
                updated_at = updated_at)
    comments.append(commentObj)
  return True


def extractGroupCommitData(url, token, alias):
  commit_data = {}
  request = urllib.request.Request(url, headers={"Authorization" : "token "+token})
  v = urllib.request.urlopen(request).read()
  j = json.loads(v.decode())
  if not j: 
    return False

  commit_data = {}

  i = 0
  for contributor in j:
    i += 1
    for week in contributor["weeks"]:
      #week_time = week["w"]
      week_time = datetime.datetime.fromtimestamp(int(week["w"])).strftime('%m-%d')
      week_additions = week["a"]
      week_commits = week["c"]

      if week_time in commit_data:
        week_dict = commit_data[week_time]
        week_dict['commits'] += week_commits
        week_dict['additions'] += week_additions
        week_dict[str(i)] = week_commits

        if week_dict['commits'] != 0:
          week_dict['additions_per_commit'] = int(week_dict['additions']/ week_dict['commits'])
        else:
          week_dict['additions_per_commit'] = 0

      else:
        week_dict = {}
        week_dict['commits'] = week_commits
        week_dict['additions'] = week_additions
        week_dict[str(i)] = week_commits
        if week_dict['commits'] != 0:
          week_dict['additions_per_commit'] = int(week_dict['additions']/ week_dict['commits'])
        else:
          week_dict['additions_per_commit'] = 0       
        commit_data[week_time] = week_dict

  #write data to csv file
  filename = alias+"_commit_data" + ".csv"
  with open(filename, 'w', newline='') as outputFile:
    outputWriter = csv.writer(outputFile)
    outputWriter.writerow(["week", "commits", "additions", "additions_per_commit", "user1", "user2", "user3", "user4"])
    for x in commit_data:
      user_4 = '0'
      if'4' in commit_data[x]:
        user_4 = commit_data[x]['4']

      outputWriter.writerow([x, commit_data[x]['commits'], commit_data[x]['additions'], commit_data[x]['additions_per_commit'], commit_data[x]['1'],commit_data[x]['2'],commit_data[x]['3'], user_4 ])



def dumpMilestone(url, milestones, token):
  request = urllib.request.Request(url, headers={"Authorization" : "token "+token})
  v = urllib.request.urlopen(request).read()
  w = json.loads(v.decode())
  if not w or ('message' in w and w['message'] == "Not Found"): return False
  
  milestone = w
  identifier = milestone['id']
  milestone_id = milestone['number']
  milestone_title = milestone['title']
  milestone_description = milestone['description']

  created_at = milestone['created_at']
  due_at = milestone['due_on']
  closed_at = milestone['closed_at']

  user = milestone['creator']['login']
  open_issues = milestone['open_issues']
  closed_issues = milestone['closed_issues']
  milestoneObj = L(ident=identifier,
             m_id = milestone_id,
             m_title = milestone_title,
             m_description = milestone_description,
             created_at=created_at,
             due_at = due_at,
             closed_at = closed_at,
             user = user,
             open_issues = open_issues,
             closed_issues = closed_issues)

  milestones.append(milestoneObj)
  return True

def dumpComments(u,comments,token):
  try:
    return dumpComments(url,comments,token)
  except Exception as e:
    print(url)
    print(e)
    print("Contact TA")
    return False

def extractGroupMilestoneData(url, token, alias):
  milestones = []
  page = 1
  while(True):

    milestone_url = url + "/" + str(page)
    print(url)
    doNext = False
    try:
      doNext = dumpMilestone(milestone_url, milestones, token)
    except Exception as e:
      print("Exception")
      doNext = False

    print("milestone "+ str(page))
    page = page + 1
    if not doNext: 
      break

  #write data to csv file
  file = alias+"_milestone_data" + ".csv"
  with open(file, 'w', newline='') as outputFile:
    outputWriter = csv.writer(outputFile)
    outputWriter.writerow(["id", "opened_at", "closed_at", "due_on", "closed_issues", "open_issues"])
    for m in milestones:
      outputWriter.writerow([m.m_id, m.created_at, m.due_at, m.closed_at, m.closed_issues, m.open_issues])


def launchDump():
  repos = [
      'SE17GroupH/Zap', 
      'SE17GroupH/ZapServer',
      'harshalgala/se17-Q', 
      'NCSU-SE-Spring-17/SE-17-S', 
      ]

  # with open("private_mappings.csv", 'w', newline='') as file:
  #   outputWriter = csv.writer(file)
  #   outputWriter.writerow(['original', 'alias'])
    
  # random.shuffle(repos)

  # for index,reponame in enumerate(repos):
  #   page = 1
  #   issues, mapping = {}, {}
    
  #   repo_url = 'https://api.github.com/repos/{}/issues/events?page='.format(reponame)+'{}'
  #   print(repo_url);
  #   while(dump(repo_url.format(page), issues, mapping)):
  #     page += 1
    
  #   group_id = "group{}".format(index+1)
  #   with open("private_mappings.csv", 'a', newline='') as file:
  #     outputWriter = csv.writer(file)
  #     outputWriter.writerow([reponame, group_id])
  #     for username, user_id in mapping.items():
  #       outputWriter.writerow([username, user_id])

  #   filename = group_id+"_issues_data"+".csv"
  #   with open(filename, 'w', newline='') as outputFile:
  #     outputWriter = csv.writer(outputFile)
  #     outputWriter.writerow(["issue_id", "when", "action", "what", "user", "milestone","assignee","comments","issuecreated_at","issueclosed_at","duration"])
  #     for issue, events in issues.items():
  #       for event in events: 
  #         outputWriter.writerow([issue, event.when, event.action, event.what, event.user, event.milestone,event.assignee,event.comments,event.issuecreated_at,secs(event.issueclosed_at),event.duration/(3600*24)])


    #commit
    #commit_repo = 'https://api.github.com/repos/{}/stats/contributors'.format(reponame)
    #extractGroupCommitData(commit_repo, token, group_id)

    #milestone
    #milestone_repo = 'https://api.github.com/repos/{}/milestones'.format(reponame)
    #extractGroupMilestoneData(milestone_repo, token, group_id)

    #comment
    #comment_repo = 'https://api.github.com/repos/repos/{}/issues/comments?page='+str(page)
    #extractGroupCommentData(comment_repo, group_id, token)
launchDump()