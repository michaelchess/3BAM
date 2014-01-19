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
		commandTwo = "pseq . lookup --file varList --loc genes --locdb locdb.genes | grep loc_genes | awk '$3!=\".\"'"
		#splitComOne = commandOne.split()
		#splitComTwo = commandTwo.split()
		comOneOut = subprocess.Popen(commandOne, stdout=subprocess.PIPE, shell=True)
		oneOut, oneErr = comOneOut.communicate()
		comTwoOut = subprocess.Popen(commandTwo, stdout=subprocess.PIPE, shell=True)
		dout, derr = comTwoOut.communicate()
		mutInfo = dout.split('\n')
		print dout
		for mut in mutInfo:
			mutParts = mut.split()
			if mut.find('#')==-1 and len(mutParts)==3:
				geneInfo = mutParts[2].rsplit(':', 1)
				mutation = models.Mutation(locus=mutParts[0], geneLoci=geneInfo[0], gene=geneInfo[1], author = user)
				db.session.add(mutation)
		db.session.commit()
			
		'''
		command = "pseq "+dataName+" v-view"
		args = command.split()
		output = subprocess.Popen(args, stdout=subprocess.PIPE, shell=False)
		dout, derr = output.communicate()
		genomeInfo = dout.split('\n')
		db.session.rollback()
		for mutation in genomeInfo:
			#print 'mutation: '
			#print mutation
			mutParts = mutation.split()
			if len(mutParts) > 1:
				print 'mutParts :'
				print mutParts
				locus = mutParts[0].split(':')
				#print "locus: "
				#print locus
				chrNum=locus[0].split('chr')[1]
				mut = models.Mutation(chromosome=chrNum, variant_ID=mutParts[1], base_position=locus[1], ref_alt_allele=mutParts[2], sample_file_identifier=mutParts[3], num_samples_observed_in=mutParts[4], author = user)
				p = models.Post(body=mutParts[3], timestamp=datetime.datetime.utcnow(), author=user)
				db.session.add(p)
				print 'the mut'
				print mut
		db.session.commit()
		print 'MUTATIONS AFTER ADDING'
		print user.mutations.all()
		'''
		return render_template('user.html', user = user, variants = user.mutations.all(), genomeInfo = mutInfo, loggedInAs = g.user.nickname)

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
		for gene in ACMGGenes:
			if gene.find(str(var.gene)) != -1:
				if ACMGVars.count(gene) <= 0:
					print gene
					#print var
					ACMGVars.append(gene)
	print '$$$$$ ACMGVars'
	print ACMGVars
	return render_template('ACMGVariants.html', ACMGVars = ACMGVars)
	#return redirect(url_for('user', user = g.user, nickname = g.user.nickname))

@login_required
@app.route('/user/otherHealthVariants')
def otherHealthVariants():
	print 'Other Health Variants'
	GeneCardsFile = open('GeneCardsList.txt', 'r')
	GeneCardsGenes = GeneCardsFile.read().split('\n')
	user=g.user
	allVariants = user.mutations.all()
	GeneCardsVars = []
	for var in allVariants:
		for gene in GeneCardsGenes:
			if gene.find(str(var.gene)) != -1:
				if GeneCardsVars.count(gene) == 0:
					#print gene
					GeneCardsVars.append(gene)
	print '@@@@@@ GeneCardsVars'
	print GeneCardsVars
	return render_template('GeneCardsVars.html', GeneCardsVars = GeneCardsVars)
	#return redirect(url_for('user', user = g.user, nickname = g.user.nickname))

@login_required
@app.route('/user/otherVariants')
def otherVariants():
	print 'Other Variants'
	return redirect(url_for('user', user = g.user, nickname = g.user.nickname))

@login_required
@app.route('/about')
def about():
	print 'About'
	return redirect(url_for('user', user = g.user, nickname = g.user.nickname))
