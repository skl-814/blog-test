from datetime import datetime
from zoneinfo import ZoneInfo
from app import db
from sqlalchemy.orm import Mapped, mapped_column

_datetimenow = lambda: datetime.now(ZoneInfo("Asia/Shanghai"))

# uni user
class User(db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)

    # the unique identifier for a user, but may not use for premission related operation
    uuid: Mapped[str] = db.Column(db.String(32), nullable=False, index=True)

    # zh_cn or en alphabet, number or _ available
    # this need some logic to restrict, especially for < and >
    user_name: Mapped[str] = db.Column(db.String(128), nullable=False, unique=True, index=True)
    ## optional # email address, maybe some email notifacation service in the future
    email :Mapped[str] = db.Column(db.String(128), nullable=True, unique=True, index=True)
    ## optional # for persional phone number, reserved for future use (maybe for register or message notification or for premission related operation)
    phone_number :Mapped[str] = db.Column(db.String(20))

    # the time that the user account is created
    created_at :Mapped[datetime] = db.Column(db.DateTime, nullable=True, default=_datetimenow)
    # the time that the user's info is modified
    modified_at :Mapped[datetime] = db.Column(db.DateTime, nullable=True, default=_datetimenow, )
    # currently sha2-256 is enough, maybe sha3-256, argon2 in the future
    password_hash :Mapped[str] = db.Column(db.String(256), nullable=False)

    # this decide the identiy of the user, and the corresponding premission. 
    # currently may only visiter. the not listed number is reserved for future use
    ##  0~ 9 # 0 for visiter(tihs is a special account level,and it store all data of visitor), 2 for common user (pubilc)
    ## 10~19 # 11 for junior manager, 13 for senior mamager, (student or teacher or else)
    ## 20~29 # 25 for teacher (admin), 
    ## 30~39 # 31 for tech admin
    role :Mapped[int] = db.Column(db.Integer, nullable=False, default=0)
    # login status, for security reason
    login :Mapped[bool]= db.Column(db.Boolean, nullable=False, default=False)
    # ipv4 addr of the last login ip of user, for security reason
    ##note: maybe imporvement of ip storage form is needed
    last_login_ip :Mapped[str] = db.Column(db.String(16), nullable=True, default='---.---.---.---')
    # temperarlly set the user is active or not
    ##note: remember to active the user after register
    active :Mapped[bool] = db.Column(db.Boolean, default=False)

    uploaded_files = db.relationship("File", back_populates="uploader")
    uploaded_public_resources = db.relationship("PublicResources", back_populates="uploader")
    posts = db.relationship("Post", back_populates="uploader")

    def __repr__(self) -> str:
        return f"<User {self.user_name} role={self.role} uuid={self.uuid} {'active' if self.active else 'deactive'}>"

# info of every user uploaded file stored
class File(db.Model):
    __tablename__ = 'files'
    id :Mapped[int]= db.Column(db.Integer, nullable=False, primary_key=True)
    # the oroginal filename
    file_name :Mapped[str] = db.Column(db.String(255), nullable=False, index=True)
    # sha2-256 hex
    file_hash :Mapped[str] = db.Column(db.String(64), nullable=False, unique=True, index=True)
    # the size of file
    file_size :Mapped[int] = db.Column(db.Integer, nullable=False, default=0)
    # 0 for local, 1 for OSS (cloudflare R2), 2 for OSS (qiniuyun)
    storage_type :Mapped[int] = db.Column(db.Integer, nullable=False)
    # path of storage, local/internet url or OSS object key
    storage_path :Mapped[str] = db.Column(db.String(512), nullable=False)
    mime_type :Mapped[str] = db.Column(db.String(128), nullable=False,)
    # counter for reference. for performance or storage optimization
    ref_count :Mapped[int] = db.Column(db.Integer, nullable=False, default=0)
    # when it is created
    created_at :Mapped[datetime] = db.Column(db.DateTime, default=_datetimenow)
    # the last modifid time
    update_at :Mapped[datetime] = db.Column(db.DateTime, default=_datetimenow, onupdate=_datetimenow)

    uploaded_by :Mapped[int] = db.Column(db.Integer, db.ForeignKey("users.id"))
    uploader = db.relationship("User", back_populates="uploaded_files")

    posts = db.relationship("Post", back_populates="files")
    post_cover = db.relationship("Post", back_populates="post_cover")
    post_attachment_file = db.relationship("Post", back_populates="attachment_file")
    asset_of_posts = db.relationship("Post", secondary="post_assets", back_populates="assets")

    def __repr__(self) -> str:
        return f"<File {self.mime_type} {self.storage_type} filename={self.file_name} at {self.update_at}>"

# table to store the asset needed by the posts
post_assets = db.Table(
    "post_assets",
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id"), primary_key=True),
    db.Column("file_id", db.Integer, db.ForeignKey("files.id"), primary_key=True)
)

# the post article
class Post(db.Model):
    __tablename__ = 'posts'
    # id
    id :Mapped[int] = db.Column(db.Integer, nullable=False, primary_key=True)
    # the file obj
    file_id :Mapped[int] = db.Column(db.Integer, db.ForeignKey("files.id"), nullable=False)
    file = db.relationship("File", foreign_keys=[file_id], back_populates="posts")
    ###### basic info of post
    # the cover of the post.please return to de default cover file if it's null
    cover_file_id :Mapped[int] = db.Column(db.Integer, db.ForeignKey("files.id"), nullable=True)
    cover_file = db.relationship("File",foreign_keys=[cover_file_id], back_populates='post_cover')
    # title of post
    title :Mapped[str] = db.Column(db.String(256), nullable=False, unique=True, index=True)
    # author(s)
    # for multi-author,please split the names by ','
    author :Mapped[str] = db.Column(db.String(64), nullable=False, default="佚名", index=True)
    ## optional # short description of the post
    description :Mapped[str] = db.Column(db.Text)
    # category of the post's field: 教授校友采访，科普，企业探访，...
    field_category_id :Mapped[int] = db.Column(db.Integer, db.ForeignKey("field_categories.id"), nullable=False, index=True)
    field_category = db.relationship("FieldCategory", back_populates="posts")
    # category of the post: 新闻，公告，...（本条目待定，暂时均设为 新闻）
    post_category_id :Mapped[int] = db.Column(db.Integer, db.ForeignKey("post_categories.id"), nullable=False, index=True)
    post_category = db.relationship("PostCategory", back_populates="posts")

    # assets, like images
    assets = db.relationship("File", secondary=post_assets, back_populates='asset_of_posts')

    # for optional attachment
    attachment_file_id :Mapped[int] = db.Column(db.Integer, db.ForeignKey("files.id"), nullable=True, )
    attachment_file = db.relationship("File",foreign_keys=[attachment_file_id], back_populates="post_attachment_file")

    ##same as File # when it is created
    created_at :Mapped[datetime] = db.Column(db.DateTime, default=_datetimenow)
    ##same as File # the last modifid time
    update_at :Mapped[datetime] = db.Column(db.DateTime, default=_datetimenow, onupdate=_datetimenow)

    uploader_id :Mapped[int]= db.Column(db.Integer, db.ForeignKey("files.id"), nullable=False)
    uploader = db.relationship("User", back_populates="posts")

    # True to show for everyone. False then only the uploader and user with higher premission can see it
    is_public :Mapped[bool] = db.Column(db.Boolean, nullable=False, default=False, index=True)

    def __repr__(self) -> str:
        return f"<Post title={self.title} {self.author} {self.field_category}/{self.post_category} by {self.uploader} at {self.update_at}>"

# type of social practice direction
class FieldCategory(db.Model):
    __tablename__ = 'field_categories'
    id :Mapped[int] = db.Column(db.Integer, nullable=False, primary_key=True)
    name :Mapped[str] = db.Column(db.String(32), nullable=False, unique=True)

    posts = db.relationship("Post", back_populates="field_category")

    def __repr__(self) -> str:

        return f"<FieldCategory {self.id} {self.name}>"
# category of post itself
class PostCategory(db.Model):
    __tablename__ = 'post_categories'
    id :Mapped[int] = db.Column(db.Integer, nullable=False, primary_key=True)
    name :Mapped[str] = db.Column(db.String(32), nullable=False, unique=True)

    posts = db.relationship("Post", back_populates="post_category")

    def __repr__(self) -> str:
        return f"<PostCategory {self.id} {self.name}>"

class PublicResources(db.Model):
    __tablename__ = "public_resources"
    id :Mapped[int] = db.Column(db.Integer, nullable=False, primary_key=True)
    file_id :Mapped[int] = db.Column(db.Integer, db.ForeignKey("files.id"), nullable=False, unique=True)
    title :Mapped[str] = db.Column(db.String(512), nullable=False)
    description :Mapped[str] = db.Column(db.Text, nullable=True, default="this is a public resource")
    category :Mapped[str] = db.Column(db.String(64), nullable=False, default="Material Science")
    is_pubilc :Mapped[bool] = db.Column(db.Boolean, nullable=False, default=True)

    file = db.relationship("File", backref="public_resources")
    uploaded_by :Mapped[int] = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    uploader = db.relationship("User", back_populates="uploader")

    def __repr__(self) -> str:
        return f"<PublicResource id={self.id} title={self.title} category={self.category} by {self.uploader}"
    