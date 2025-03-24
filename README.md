# ENEZA ELIMU - School Management System

A comprehensive school management system built with Django that helps schools track student performance, manage academic terms, and analyze subject-wise performance metrics.

## 🎯 Features

### Academic Management
- Class management with multiple streams
- Term-wise academic tracking
- Subject-wise performance analysis
- Student performance tracking
- CAT (Continuous Assessment Tests) management

### Analytics & Reporting
- Subject-wise performance visualization
- Class performance analytics
- Term-by-term comparison
- Interactive charts and graphs
- Detailed performance reports

### User Interface
- Clean, responsive design using Tailwind CSS
- Interactive data visualization using Plotly.js
- Intuitive navigation between classes, terms, and subjects
- Mobile-friendly layout

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Django 4.0 or higher
- PostgreSQL (recommended) or SQLite

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/eneza-elimu.git
cd eneza-elimu
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure environment variables
```bash
cp .env.example .env
# Edit .env file with your database and other settings
```

5. Run migrations
```bash
python manage.py migrate
```

6. Create superuser
```bash
python manage.py createsuperuser
```

7. Run development server
```bash
python manage.py runserver
```

## 📋 Project Structure

```
eneza_elimu/
├── manage.py
├── school/                 # Main application
│   ├── models.py          # Database models
│   ├── views.py           # View functions
│   ├── urls.py           # URL configurations
│   └── templates/        # HTML templates
│       └── school/
│           ├── class_list.html
│           ├── term_list.html
│           └── subject_analysis.html
├── static/               # Static files
│   ├── css/
│   └── js/
└── templates/           # Base templates
```

## 💻 Technology Stack

- **Backend:** Django
- **Database:** PostgreSQL/SQLite
- **Frontend:** 
  - HTML5
  - Tailwind CSS
  - JavaScript
  - Plotly.js for charts
- **Development Tools:**
  - Git for version control
  - pip for package management

## 📊 Data Models

### Class_of_study
- name: Class name (e.g., Form 1, Form 2)
- stream: Class stream (e.g., East, West)

### Term
- name: Term name (e.g., Term 1, Term 2)
- year: Academic year
- start_date: Term start date
- end_date: Term end date

### Subject
- name: Subject name
- code: Subject code

### CAT (Continuous Assessment Tests)
- student: ForeignKey to Student
- subject: ForeignKey to Subject
- term: ForeignKey to Term
- end_term: End term marks

## 🛠️ Configuration

### Environment Variables
```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/eneza_elimu
```

## 🔒 Security

- Django's built-in security features
- CSRF protection
- SQL injection prevention
- XSS protection
- Secure password hashing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- Steve Ongera - Initial work

## 🙏 Acknowledgments

- Django Documentation
- Tailwind CSS
- Plotly.js
- All contributors who helped with the project

## 📞 Support

For support, email steveongera001@gmail.com or create an issue in the repository.

---

**Note:** This is a school project developed for educational purposes. Feel free to use and modify according to your needs.