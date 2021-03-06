from flask import render_template, flash, redirect, session, url_for, request, g, \
	send_from_directory, send_file, Response
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid, models
from forms import LoginForm
from models import User, ROLE_USER, ROLE_ADMIN
from werkzeug import secure_filename
import os
import StringIO
import subprocess
import datetime

ALLOWED_EXTENSIONS = set(['txt', 'vcf'])

def allowedFile(filename):
	#checks if uploaded file is of the correct type
	return '.' in filename and \
		filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user

@app.route('/')
@app.route('/index')
def index():
    user = g.user
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('user', user = user, nickname = user.nickname))
    else:
    	return render_template('main_banner.html')


@app.route('/login', methods = ['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('user', user = g.user, nickname = g.user.nickname))
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        return oid.try_login(form.openid.data, ask_for = ['nickname', 'email'])
    return render_template('login.html', 
        title = 'Sign In',
        form = form,
        providers = app.config['OPENID_PROVIDERS'])


@oid.after_login
def after_login(resp):
    if resp.email is None or resp.email == "":
        flash('Invalid login. Please try again.')
        return redirect(url_for('login'))
    user = User.query.filter_by(email = resp.email).first()
    if user is None:
        nickname = resp.nickname
        if nickname is None or nickname == "":
            nickname = resp.email.split('@')[0]
        user = User(nickname = nickname, email = resp.email, role = ROLE_USER)
        db.session.add(user)
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember = remember_me)
    return redirect(request.args.get('next') or url_for('index'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/user/<nickname>')
@login_required
def user(nickname):
    user = User.query.filter_by(nickname = nickname).first()
    if user == None:
        flash('User ' + nickname + ' not found.')
        return redirect(url_for('index'))
    user = g.user
    
    return render_template('user.html', user = user, variants = user.mutations.all(), genomeInfo = None, loggedInAs = g.user.nickname)


@app.route('/upload', methods=['GET', 'POST'])
def uploadGenome():
	if request.method == 'POST':
		userGenome = request.files['userGenome']
		if userGenome and allowedFile(userGenome.filename):
			dataName = secure_filename(userGenome.filename)
			userGenome.save(os.path.join(app.config['UPLOAD_FOLDER'], dataName))
		else:
			return "Your file was of an incorrect type, please change file type to .txt and try again."
		#genomeFile = open(dataName, 'r')
		#genomeInfo = genomeFile.read()
		user = g.user
		commandOne = "grep -v \# "+os.path.join(app.config['UPLOAD_FOLDER'], dataName)+" | awk '{OFS=\"\";print \"chr\",$1,\":\",$2}\' > varList"
		#commandTwo = "pseq . lookup --file varList --loc genes --locdb locdb.genes | grep loc_genes | awk \'$3!=\".\"\'"
		commandTwo = "pseq . lookup --file varList --loc genes --locdb locdb.genes | grep loc_genes"# | awk '$3!=\".\"'"
		#splitComOne = commandOne.split()
		#splitComTwo = commandTwo.split()
		comOneOut = subprocess.Popen(commandOne, stdout=subprocess.PIPE, shell=True)
		oneOut, oneErr = comOneOut.communicate()
		comTwoOut = subprocess.Popen(commandTwo, stdout=subprocess.PIPE, shell=True)
		dout, derr = comTwoOut.communicate()
		varInfo = dout.split('\n')
		print dout
		for var in varInfo:
			varParts = var.split()
			if var.find('#')==-1 and len(varParts)==3:
				geneInfo = varParts[2].rsplit(':', 1)
				if len(geneInfo) == 1:
					variant = models.Mutation(locus=varParts[0], geneLoci=geneInfo[0], gene=geneInfo[0], author = user)
				else:
					variant = models.Mutation(locus=varParts[0], geneLoci=geneInfo[0], gene=geneInfo[1], author = user)
				db.session.add(variant)
		db.session.commit()
		GeneCardsFile = open('GeneCardsList.txt', 'r')
		GeneCardsGenes = GeneCardsFile.read().split('\n')
		user=g.user
		allVariants = user.mutations.all()
		GeneCardsVars = []
		for var in allVariants:
			if var.gene != '.':
				for gene in GeneCardsGenes:
					if gene.find(str(var.gene)) != -1:
						if GeneCardsVars.count(gene.split('\t')) == 0:
							GeneCardsVars.append(gene.split('\t'))
		print '@@@@@@ GeneCardsVars'
		#print GeneCardsVars
		user.GeneCardsVariants = GeneCardsVars
		db.session.commit()
		print user.GeneCardsVariants
		return render_template('user.html', user = user, variants = user.mutations.all(), genomeInfo = varInfo, loggedInAs = g.user.nickname)

@login_required
@app.route('/user/home')
def home():
	print 'Home'
	return redirect(url_for('user', user = g.user, nickname = g.user.nickname))
	
@login_required
@app.route('/user/ACMGVariants')
def ACMGVariants():
	print 'ACMG Variants'
	ACMGGenesFile = open('mandatoryReporting.txt', 'r')
	ACMGGenes = ACMGGenesFile.read().split('\n')
	user = g.user
	allVariants = user.mutations.all()
	ACMGVars = []
	for var in allVariants:
		if var.gene != '.':
			for gene in ACMGGenes:
				if gene.find(str(var.gene)) != -1:
					if ACMGVars.count(gene.split('\t')) == 0:
						#print ACMGVars.count(gene)
						#print gene
						#print var
						ACMGVars.append(gene.split('\t'))
	print '$$$$$ ACMGVars'
	print ACMGVars
	return render_template('ACMGVariants.html', ACMGVars = ACMGVars)
	#return redirect(url_for('user', user = g.user, nickname = g.user.nickname))

@login_required
@app.route('/user/otherHealthVariants')
def otherHealthVariants():
	print 'Other Health Variants'
	user = g.user
	GeneCardsVars = user.GeneCardsVariants
	'''GeneCardsFile = open('GeneCardsList.txt', 'r')
	GeneCardsGenes = GeneCardsFile.read().split('\n')
	user=g.user
	allVariants = user.mutations.all()
	GeneCardsVars = []
	for var in allVariants:
		for gene in GeneCardsGenes:
			if gene.find(str(var.gene)) != -1:
				if GeneCardsVars.count(gene.split('\t')) == 0:
					GeneCardsVars.append(gene.split('\t'))
    
	for gene in GeneCardsGenes:
		if GeneCardsVars.count(gene.split('Show')[0].split('\t')) == 0:
			for var in allVariants:
				if gene.find(str(var.gene)) != -1:
					#print gene
					GeneCardsVars.append(gene.split('Show')[0].split('\t'))'''
	print '@@@@@@ GeneCardsVars'
	
	#for line in GeneCardsVars:
	#	line = line.split('\t')
	print GeneCardsVars
	return render_template('GeneCardsVars.html', GeneCardsVars = GeneCardsVars)
	#return redirect(url_for('user', user = g.user, nickname = g.user.nickname))

@login_required
@app.route('/user/otherVariants')
def otherVariants():
	print 'Other Variants'
	user = g.user
	allVars = user.mutations.all()
	return render_template('AllVariantsPage.html', allVars = allVars)
	#return redirect(url_for('user', user = g.user, nickname = g.user.nickname))

@login_required
@app.route('/about')
def about():
	print 'About'
	return render_template('about.html')
	#return redirect(url_for('user', user = g.user, nickname = g.user.nickname))
