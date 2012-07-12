#-*- coding:utf-8 -*-
from flask import g, render_template,request,url_for,redirect, session

from chartnet import app
from chartnet import setting
from models import operatorDB
from common import login_required
import re
import time
#from sae.const import (MYSQL_HOST, MYSQL_HOST_S,MYSQL_PORT, MYSQL_USER, MYSQL_PASS, MYSQL_DB)

@app.before_request
def before_request():
	#appinfo = sae.core.Application()
	#g.db = MySQLdb.connect(MYSQL_HOST, MYSQL_USER, MYSQL_PASS,MYSQL_DB, port=int(MYSQL_PORT)
	pass

@app.teardown_request
def teardown_request(exception):
	if hasattr(g,'db') : g.db.close()

@app.route('/')
def _index():
	posts = None
	_newer = False
	_older = False
	_start = 0
	_end = 0
	if request.args.get('_start','')!='' :
		_start = int(request.args.get('_start',''))
	_end = _start+setting.EACH_PAGE_POST_NUM
	if request.args.get('cat','')!='' :
		posts = operatorDB.get_post_page_category(_start,_end,request.args.get('cat',''))
	elif request.args.get('tags','')!='' :
		posts = operatorDB.get_post_page_tags(_start,_end,request.args.get('tags',''))
	else :
		posts,_newer,_older = operatorDB.get_post_page(_start,_end)
	return render_template('index.html',_newstart=_start-setting.EACH_PAGE_POST_NUM,_oldstart=_end,_newer=_newer,_older=_older,posts=posts,coms=operatorDB.get_comments_new(),tags = operatorDB.get_all_tag_name(),cats=operatorDB.get_all_cat_name(),links=operatorDB.get_all_links(),BASE_URL=setting.BASE_URL)

@app.route('/detailpost/<int:post_id>', methods=['GET', 'POST'])
def detailpost(post_id):
	if request.method == 'POST':
		operatorDB.add_new_comment(post_id,request.form.get('author', ''),request.form.get('email', ''),request.form.get('url', ''),1,request.form.get('comment', ''))
	_article = operatorDB.detail_post_by_id(post_id)
	comments = operatorDB.get_post_comments(post_id)
	comLen = len(comments)
	return render_template('detailpost.html',coms=operatorDB.get_comments_new(),tags = operatorDB.get_all_tag_name(),cats=operatorDB.get_all_cat_name(),links=operatorDB.get_all_links(),post_id=post_id,comLen=comLen,comments=comments,obj=_article,add_time=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(_article._add_time)))

@app.route('/about', methods=['GET', 'POST'])
def _about():
	if request.method == 'POST':
		operatorDB.insertAboutReply(request.form.get('author', ''),request.form.get('email', ''),request.form.get('url', ''),request.form.get('comment', ''))
	aboutReplys = operatorDB.getAboutReplyAll()
	aboutReplysLen = len(aboutReplys)
	return render_template('about.html',tags = operatorDB.get_all_tag_name(),cats=operatorDB.get_all_cat_name(),links=operatorDB.get_all_links(),sub_category=setting.HEAD_SUBCATEGORY['about'],aboutReplys=aboutReplys,aboutReplysLen=aboutReplysLen,BASE_URL=setting.BASE_URL)

@app.route('/soGoodorBad')
def _soGoodorBad():
	if request.args['action']=='so_good':
		operatorDB.addSogood(request.args['id'])
	if request.args['action']=='so_bad':
		operatorDB.addSobad(request.args['id'])
	return redirect(url_for('_about'))

#管理员
@app.route('/admin/index')
@login_required
def admin_index():
	return render_template('admin/index_admin.html',title=u'后台管理',SITE_TITLE=setting.SITE_TITLE,BASE_URL=setting.BASE_URL)

@app.route('/admin/logout')
def admin_logout():
	session.pop('username', None)
	return render_template('admin/login_admin.html',has_user=operatorDB.has_user(),title=u'管理员登录',SITE_TITLE=setting.SITE_TITLE,BASE_URL=setting.BASE_URL)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
	if request.method == 'POST':
		if not operatorDB.has_user():
			operatorDB.add_user(request.form.get('name', ''),request.form.get('password', ''))
			session['username'] = request.form.get('name', '')
			return redirect(url_for('admin_index'))
		if operatorDB.login_user(request.form.get('name', ''),request.form.get('password', '')):			 
			session['username'] = request.form.get('name', '')
			return redirect(url_for('admin_index'))
	return render_template('admin/login_admin.html',has_user=operatorDB.has_user(),title=u'管理员登录',SITE_TITLE=setting.SITE_TITLE,BASE_URL=setting.BASE_URL)

@app.route('/admin/links', methods=['GET', 'POST'])
@login_required
def admin_links():
	obj = None
	if request.method == 'POST':
		act = request.form['act']
		if act == 'add':
			operatorDB.add_new_link(request.form.get('name', ''),request.form.get('sort', ''),request.form.get('url', ''))
		if act == 'edit':
			operatorDB.update_link_edit(request.form.get('id', ''),request.form.get('name', ''),request.form.get('sort', ''),request.form.get('url', ''))
	if request.method == 'GET':
		act = request.args.get('act', '')
		if act == 'del': 
			operatorDB.del_link_by_id(request.args.get('id', ''))
		if act == 'edit':
			obj = operatorDB.get_link_by_id(request.args.get('id', ''))
	return render_template('admin/link_admin.html',obj=obj,objs=operatorDB.get_all_links(),title=u'友情链接管理',SITE_TITLE=setting.SITE_TITLE,BASE_URL=setting.BASE_URL)

@app.route('/admin/add_post', methods=['GET', 'POST'])
@login_required
def admin_addpost():
	if request.method == 'POST':
		_tags = request.form.get('tags', '').replace(u'，',',')
		tagslist = set([x.strip() for x in _tags.split(',')])
		try:
			tagslist.remove('')
		except:
			pass
		if tagslist:
			_tags = ','.join(tagslist)
		postId = operatorDB.add_new_article(request.form.get('category', ''),request.form.get('title', ''),request.form.get('content', ''),_tags,request.form.get('password', ''),shorten_content(request.form.get('content', '')))
		if _tags!='':
			operatorDB.add_postid_to_tags(_tags.split(','), str(postId))
		operatorDB.add_postid_to_cat(request.form.get('category', ''),str(postId))	
	cats = operatorDB.get_all_cat_name()
	tags = operatorDB.get_all_tag_name()
	return render_template('admin/addpost_admin.html',title=u'添加文章',cats=cats,tags=tags,SITE_TITLE=setting.SITE_TITLE,BASE_URL=setting.BASE_URL)

@app.route('/admin/edit_post',methods=['GET', 'POST'])
@login_required
def admin_editpost():
	_article = None
	if request.method == 'POST':
		if request.form.get('act', '')=='editpost':
			_tags = request.form.get('tags', '').replace(u'，',',')
			tagslist = set([x.strip() for x in _tags.split(',')])
			try:
				tagslist.remove('')
			except:
				pass
			if tagslist:
				_tags = ','.join(tagslist)
			operatorDB.update_article(request.form.get('id', ''),request.form.get('category', ''),request.form.get('title', ''),request.form.get('content', ''),_tags,request.form.get('password', ''),shorten_content(request.form.get('content', '')))
		post_id = request.form.get('id', '')
		_article = operatorDB.detail_post_by_id(post_id)
	cats = operatorDB.get_all_cat_name()
	tags = operatorDB.get_all_tag_name()
	return render_template('admin/editpost_admin.html',obj=_article,cats=cats,tags=tags)

@app.route('/admin/del_post/<int:post_id>')
@login_required
def admin_delpost(post_id):
	operatorDB.del_post_by_id(post_id)
	return redirect(url_for('admin_editpost'))

def shorten_content(htmlstr='',sublength=80):
	result = re.sub(r'<[^>]+>', '', htmlstr)
	return result[0:sublength]