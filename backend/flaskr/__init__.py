from multiprocessing.dummy import current_process
import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def get_paginated_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app, resources={'/': {'origins': '*'}})

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response
    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """

    @app.route('/categories', methods=['GET'])
    def retrieve_categories():
        try:
            categories = Category.query.order_by(Category.id).all()
            return jsonify({
                'categories': {category.id:category.type for category in categories},
                'success': True,
            }) 
        except:
            abort(404)

    @app.route('/questions', methods=['GET'])
    def retrieve_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = get_paginated_questions(request, selection)

        categories = Category.query.order_by(Category.type).all()

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(Question.query.all()),
            'categories': {category.id: category.type for category in categories},
            'current_category': None
        })

    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = get_paginated_questions(request, selection)

            return jsonify(
                {
                    "success": True,
                    "deleted": question_id,
                    "question": current_questions,
                    "total_questions": len(Question.query.all()),
                }
            )

        except:
            abort(422)

    @app.route('/questions', methods=['POST'])
    def create_new_question():
        body = request.get_json()

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)

        try:
            question = Question(
            question=new_question,
            answer=new_answer,
            category=new_category,
            difficulty=new_difficulty
            )
            question.insert()
            selection = Question.query.order_by(Question.id).all()
            current_questions = get_paginated_questions(request, selection)

            return jsonify({
                'success': True,
                'created': question.id,
                'questions': current_questions,
                'total_questions': len(selection)
            })
        except:
            abort(422)


    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        body = request.get_json() 
        search = body.get('searchTerm', None)
        try:
            search_questions = Question.query.filter(Question.question.ilike("%{}%".format(search))).all()
            current_questions = get_paginated_questions(
                request, search_questions)
            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(search_questions)
            })
        except:
            abort(422)

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id): 
        try:
            category = Category.query.filter(Category.id == category_id).one_or_none()

            if category is None:
                abort(404)
            questions_selection = Question.query.order_by(Question.id).filter(Question.category == category_id).all()
            questions = get_paginated_questions(request, questions_selection)

            return jsonify({
                'success': True,
                'questions': questions,
                'total_questions': len(questions_selection),
                'current_category': category.type
            })
        except:
            abort(404)
     
    @app.route('/quizzes', methods=['POST'])
    def the_quiz():
        try:
            body = request.get_json()

            category = body.get('quiz_category', None)
            previous_questions = body.get('previous_questions', None)
            category_id = category['id']

            if category_id == 0:
                available_questions = Question.query.filter(Question.id.notin_((previous_questions))).all()

            else:
                available_questions = Question.query.filter_by(category=category_id).filter(Question.id.notin_((previous_questions))).all()
            new_question = available_questions[random.randrange(0, len(available_questions))].format() if len(available_questions) > 0 else None

            return jsonify({
                'success': True,
                'question': new_question
            })
        except:
            abort(422)
    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            'error': 400,
            "message": "Bad request"
        }), 400

    @app.errorhandler(404)
    def page_not_found(error):
        return jsonify({
            "success": False,
            'error': 404,
            "message": "Page not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable_resource(error):
        return jsonify({
            "success": False,
            'error': 422,
            "message": "Unprocessable resource"
        }), 422

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "success": False,
            'error': 500,
            "message": "Internal server error"
        }), 500

    @app.errorhandler(405)
    def invalid_method(error):
        return jsonify({
            "success": False,
            'error': 405,
            "message": "Invalid method!"
        }), 405

    return app
