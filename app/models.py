from app import db

ROLE_USER = 0
ROLE_ADMIN = 1

class User(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	nickname = db.Column(db.String(64), index = True, unique = True)
	email = db.Column(db.String(120), index = True, unique = True)
	role = db.Column(db.SmallInteger, default = ROLE_USER)
	posts = db.relationship('Post', backref = 'author', lazy = 'dynamic')
	mutations = db.relationship('Mutation', backref = 'author', lazy = 'dynamic')
	
	def is_authenticated(self):
		return True
	
	def is_active(self):
		return True
	
	def is_anonymous(self):
		return False
	
	def get_id(self):
		return unicode(self.id)
	
	def __repr__(self):
		return '<User %r>' % (self.nickname)


class Mutation(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	locus = db.Column(db.String(200), index = True)
	geneLoci = db.Column(db.String(200), index = True)
	gene = db.Column(db.String(200), index = True)
	#chromosome = db.Column(db.SmallInteger, index = True)
	#chromosome = db.Column(db.String(200), index = True)
	#variant_ID = db.Column(db.String(200), index = True, unique = True)
	#base_position = db.Column(db.Integer, index = True)
	#base_position = db.Column(db.String(200), index = True)
	#ref_alt_allele = db.Column(db.String(200), index = True)
	#sample_file_identifier = db.Column(db.String(200), index = True)
	#num_samples_observed_in = db.Column(db.SmallInteger, index = True)
	#num_samples_observed_in = db.Column(db.String(200), index = True)
	
	
	def __repr__(self):
		return '<Mutation %r>' % (self.locus)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post %r>' % (self.body)