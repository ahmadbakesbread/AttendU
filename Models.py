from sqlalchemy import Column, Integer, String, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.schema import Table
from sqlalchemy.sql.sqltypes import Date, Boolean, PickleType
from sqlalchemy.exc import SQLAlchemyError
from Helpers import image_to_encoding
import bcrypt

Base = declarative_base()

student_class_association = Table('student_class', Base.metadata,
    Column('student_id', Integer, ForeignKey('students.id', ondelete='CASCADE')),
    Column('class_id', Integer, ForeignKey('classes.id', ondelete='CASCADE'))
)

parent_student_association = Table('parent_student', Base.metadata,
    Column('parent_id', Integer, ForeignKey('parents.id')),
    Column('student_id', Integer, ForeignKey('students.id'))
)

class Class(Base):
    __tablename__ = 'classes'

    id = Column(Integer, primary_key=True)
    teacher_id = Column(Integer, ForeignKey('teachers.id'))
    class_name = Column(String(150), nullable=False)

    teacher = relationship('Teacher', back_populates='classes')
    students = relationship('Student', secondary=student_class_association, back_populates='classes')
    attendances = relationship('Attendance', back_populates='_class')


    def add_student(self, session: Session, student_id: int):
        try:
            student = session.query(Student).filter_by(id=student_id).first()
            if student is None:
                raise ValueError("Student not found")
            self.students.append(student)
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise

    # Remove a student from the class
    def remove_student(self, session: Session, student_id: int):
        try:
            student = session.query(Student).filter_by(id=student_id).first()
            if student is None:
                raise ValueError("Student not found")
            self.students.remove(student)
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise

    # Get student's profile
    def get_student_profile(self, session: Session, student_id: int):
        try:
            student = [student for student in self.students if student.id == student_id]
            if student:
                return student[0]
            else:
                raise ValueError("Student not found in this class")
        except SQLAlchemyError:
            session.rollback()
            raise


class Attendance(Base):
    __tablename__ = 'attendances'

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    attended = Column(Boolean, nullable=False)
    student_id = Column(Integer, ForeignKey('students.id'))
    class_id = Column(Integer, ForeignKey('classes.id'))

    student = relationship('Student', back_populates='attendances')
    _class = relationship('Class', back_populates='attendances')


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(60), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    image = Column(String(1000))
    password = Column(LargeBinary(60), nullable=False)
    classes = relationship('Class', back_populates='teacher')


    def __init__(self, name, email, password, image=None) -> None:
        self.name = name
        self.email = email
        self.image = image
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    def create_class(self, session: Session, class_name: str):
        try:
            session.add(Class(teacher_id=self.id, class_name=class_name))
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise

    def delete_class(self, session: Session, class_id: int):
        try:
            class_ = session.query(Class).filter_by(id=class_id, teacher_id=self.id).first()
            if class_ is None:
                raise ValueError("Class not found")
            session.execute(student_class_association.delete().where(student_class_association.c.class_id == class_id))
            session.delete(class_)
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise

    def update_profile(self, session: Session, name=None, email=None, image=None):
        try:
            if name:
                self.name = name
            if email:
                self.email = email
            if image:
                self.image = image
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise


class Parent(Base):
    __tablename__ = "parents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(60), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    image = Column(String(1000))
    password = Column(LargeBinary(60), nullable=False)
    children = relationship("Student", secondary=parent_student_association, back_populates="parents")


    def __init__(self, name, email, password, image=None) -> None:
        self.name = name
        self.email = email
        self.image = image
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    def add_child(self, session: Session, student_id: int):
        try:
            student = session.query(Student).filter_by(id=student_id).first()
            if student is None:
                raise ValueError("Student not found")
            self.children.append(student)
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise

    # Remove a child from the parent
    def remove_child(self, session: Session, student_id: int):
        try:
            student = [student for student in self.children if student.id == student_id]
            if student:
                self.children.remove(student[0])
                session.commit()
            else:
                raise ValueError("Student not found in this parent")
        except SQLAlchemyError:
            session.rollback()
            raise

    def get_children_classes(self):
        return [[_class for _class in child.classes] for child in self.children]
    
    def get_child_attendance(self, session: Session, student_id: int, class_id: int):
        try:
            attendance = session.query(Attendance).filter_by(student_id=student_id, class_id=class_id).all()
            if attendance:
                return attendance
            else:
                raise ValueError("No attendance records found for this student in this class")
        except SQLAlchemyError:
            session.rollback()
            raise

    def update_profile(self, session: Session, name=None, email=None, image=None):
        try:
            if name:
                self.name = name
            if email:
                self.email = email
            if image:
                self.image = image
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(60), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    image = Column(String(1000))
    password = Column(LargeBinary(60), nullable=False)
    face_vector = Column(PickleType, nullable=True)
    classes = relationship('Class', secondary=student_class_association, back_populates='students')
    parents = relationship("Parent", secondary=parent_student_association, back_populates="children")
    attendances = relationship('Attendance', back_populates='student')

    def __init__(self, name, email, password, image) -> None:
        self.name = name
        self.email = email
        self.image = image
        if self.image:
            self._update_face_vector()
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    def join_class(self, session: Session, class_id: int):
        try:
            class_ = session.query(Class).filter_by(id=class_id).first()
            if class_ is None:
                raise ValueError("Class not found")
            self.classes.append(class_)
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
    
    def leave_class(self, session: Session, class_id: int):
        try:
            class_ = session.query(Class).filter_by(id=class_id).first()
            if class_ is None:
                raise ValueError("Class not found")
            self.classes.remove(class_)
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise

    def get_attendance(self, session: Session, class_id: int):
        try:
            attendances = session.query(Attendance).filter_by(student_id=self.id, class_id=class_id).all()
            return attendances
        except SQLAlchemyError:
            session.rollback()
            raise

    def update_profile(self, session: Session, name=None, email=None, image=None):
        try:
            if name:
                self.name = name
            if email:
                self.email = email
            if image:
                self.image = image
                self._update_face_vector()
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
    
    def _update_face_vector(self):
        encoding = image_to_encoding(self.image)
        if encoding is not None:
            self.face_vector = encoding
        else:
            raise ValueError("Image encoding failed")
