import sys, os
from ConfigParser import SafeConfigParser
import logging
import praw
from praw.handlers import MultiprocessHandler
import datetime
from datetime import datetime, timedelta
from time import sleep, time

# load config file
containing_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
cfg_file = SafeConfigParser()
path_to_cfg = os.path.join(containing_dir, 'config.cfg')
cfg_file.read(path_to_cfg)
username = cfg_file.get('reddit', 'username')
password = cfg_file.get('reddit', 'password')
subreddit = cfg_file.get('reddit', 'subreddit')
link_id = cfg_file.get('reddit', 'link_id')
equal_warning = cfg_file.get('replies', 'equal')
age_warning = cfg_file.get('replies', 'age')
karma_warning = cfg_file.get('replies', 'karma')
added_msg = cfg_file.get('replies', 'added')

#configure logging
logging.basicConfig(level=logging.INFO, filename='actions.log')



def main():

	def conditions():
		if comment.id in completed:
			return False
		if not hasattr(comment.author, 'name'):
			return False
		if 'confirm' not in comment.body.lower():
			return False
		if comment.author.name == username:
			return False
		if comment.is_root == True:
			return False
		return True

	def check_self_reply():
		if comment.author.name == parent.author.name:
			item.reply(equal_warning)
			item.report()
			parent.report()
			save()
			return False
		return True

	def verify(item):
		karma = item.author.link_karma + item.author.comment_karma
		age = (datetime.utcnow() - datetime.utcfromtimestamp(item.author.created_utc)).days

		if item.author_flair_css_class < 1:
			if age < 14:
				item.report()
				item.reply(age_warning)
				save()
				return False
			if karma < 10:
				item.report()
				item.reply(karma_warning)
				save()
				return False
		return True

	def values(item):
		if not item.author_flair_css_class:
			item.author_flair_css_class = '1'
		elif item.author_flair_css_class and 'mod' in item.author_flair_css_class:
			pass
		else:
			item.author_flair_css_class = str(int(item.author_flair_css_class) + 1)
		if not item.author_flair_text:
			item.author_flair_text = ''

	def flair(item):
		if item.author_flair_css_class != 'mod':
			item.subreddit.set_flair(item.author, item.author_flair_text, item.author_flair_css_class)
			logging.info('Set ' + item.author.name + '\'s flair to ' + item.author_flair_css_class)

		for com in flat_comments:
			if hasattr(com.author, 'name'):
				if com.author.name == item.author.name:
					com.author_flair_css_class = item.author_flair_css_class

	def save():
		with open (link_id+".log", 'a') as myfile:
				myfile.write('%s\n' % comment.id)

	while True:
		try:
			# Load old comments
			with open (link_id+".log", 'a+') as myfile:
				completed = myfile.read()

			# Log in
			logging.info('Logging in as /u/'+username)
			r = praw.Reddit(user_agent=username)
			r.login(username, password)

			# Get the submission and the comments
			submission = r.get_submission(submission_id=link_id)
			submission.replace_more_comments(limit=None, threshold=0)
			flat_comments = list(praw.helpers.flatten_tree(submission.comments))

			for comment in flat_comments:

				if not conditions(): continue
				parent = [com for com in flat_comments if com.fullname == comment.parent_id][0]
				if not check_self_reply(): continue

				# Check Account Age and Karma
				if not verify(comment): continue
				if not verify(parent): continue

				# Get Future Values to Flair
				values(comment)
				values(parent)

				# Flairs up in here
				flair(comment)
				flair(parent)
				comment.reply(added_msg)
				save()

		# I have no idea what this does, but I need an except
		except Exception as e:
			logging.error(e)
			
		sleep(300)

if __name__ == '__main__':
    main()