import unittest
from unittest.mock import patch, MagicMock
import dukebot.tools as tools
import json

class TestTools(unittest.TestCase):
    @patch('dukebot.tools.requests.get')
    def test_get_curriculum_with_subject_from_duke_api_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = '[{"course_id": "123", "name": "Test Course"}]'
        result = tools.get_curriculum_with_subject_from_duke_api('AIPI')
        self.assertIn('Test Course', result)

    @patch('dukebot.tools.requests.get')
    def test_get_curriculum_with_subject_from_duke_api_failure(self, mock_get):
        mock_get.return_value.status_code = 404
        mock_get.return_value.text = 'Not Found'
        result = tools.get_curriculum_with_subject_from_duke_api('AIPI')
        self.assertIn('Failed to fetch data', result)

    @patch('dukebot.tools.requests.get')
    def test_get_detailed_course_information_from_duke_api_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = '{"course_id": "123", "name": "Test Course"}'
        result = tools.get_detailed_course_information_from_duke_api('123', '1')
        self.assertIn('Test Course', result)

    @patch('dukebot.tools.requests.get')
    def test_get_detailed_course_information_from_duke_api_failure(self, mock_get):
        mock_get.return_value.status_code = 500
        mock_get.return_value.text = 'Internal Server Error'
        result = tools.get_detailed_course_information_from_duke_api('123', '1')
        self.assertIn('Failed to fetch data', result)

    @patch('dukebot.tools.requests.get')
    def test_get_people_information_from_duke_api_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = '[{"name": "John Doe"}]'
        result = tools.get_people_information_from_duke_api('John Doe')
        self.assertIn('John Doe', result)

    @patch('dukebot.tools.requests.get')
    def test_get_people_information_from_duke_api_failure(self, mock_get):
        mock_get.return_value.status_code = 404
        mock_get.return_value.text = 'Not Found'
        result = tools.get_people_information_from_duke_api('John Doe')
        self.assertIn('Failed to fetch data', result)

    def test_filter_candidates(self):
        candidates = ['apple', 'banana', 'grape']
        result = tools.filter_candidates('appl', candidates)
        self.assertIn('apple', result)

    def test_load_valid_values(self):
        with patch('builtins.open', unittest.mock.mock_open(read_data='A\nB\nC\n')):
            result = tools.load_valid_values('dummy.txt')
            self.assertEqual(result, ['A', 'B', 'C'])

    def test_search_subject_by_code(self):
        tools.valid_subjects = ['AIPI - Artificial Intelligence', 'CS - Computer Science']
        result = tools.search_subject_by_code('AIPI')
        self.assertIn('AIPI', result)

    def test_search_group_format(self):
        tools.valid_groups = ['Group1', 'Group2']
        result = tools.search_group_format('Group1')
        self.assertIn('Group1', result)

    def test_search_category_format(self):
        tools.valid_categories = ['Cat1', 'Cat2']
        result = tools.search_category_format('Cat1')
        self.assertIn('Cat1', result)

    @patch('dukebot.tools.requests.get')
    @patch('dukebot.tools.logging.getLogger')
    def test_events_from_duke_api_success(self, mock_logger, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = 'ok' * 500
        result = tools.events_from_duke_api(groups=['All'], categories=['All'])
        self.assertIn('ok', result)

    @patch('dukebot.tools.requests.get')
    @patch('dukebot.tools.logging.getLogger')
    def test_events_from_duke_api_api_error(self, mock_logger, mock_get):
        mock_get.return_value.status_code = 400
        mock_get.return_value.text = 'fail'
        result = tools.events_from_duke_api(groups=['All'], categories=['All'])
        self.assertIn('Failed to fetch data', result)

    @patch('dukebot.tools.requests.get', side_effect=Exception('fail'))
    @patch('dukebot.tools.logging.getLogger')
    def test_events_from_duke_api_exception(self, mock_logger, mock_get):
        result = tools.events_from_duke_api(groups=['All'], categories=['All'])
        self.assertIn('Exception occurred', result)

    @patch('dukebot.tools.llm_map_prompt_to_filters', return_value=(['A'], ['B']))
    @patch('dukebot.tools.events_from_duke_api', return_value='result')
    def test_get_events_from_duke_api_valid(self, mock_events, mock_map):
        result = tools.get_events_from_duke_api('prompt')
        self.assertEqual(result, 'result')

    @patch('dukebot.tools.llm_map_prompt_to_filters', return_value=([], []))
    def test_get_events_from_duke_api_invalid(self, mock_map):
        result = tools.get_events_from_duke_api('prompt')
        self.assertIn('Error', result)

    @patch('dukebot.tools.get_events_from_duke_api', return_value='result')
    def test_get_events_from_duke_api_single_input_various(self, mock_events):
        # Only prompt
        self.assertIn('result', tools.get_events_from_duke_api_single_input('prompt'))
        # All params
        self.assertIn('result', tools.get_events_from_duke_api_single_input('prompt,json,30,False,False'))
        # Invalid future_days
        self.assertIn('result', tools.get_events_from_duke_api_single_input('prompt,json,notanint'))
        # filter_method_group/cat as 0
        self.assertIn('result', tools.get_events_from_duke_api_single_input('prompt,json,30,0,0'))
        # Missing prompt
        self.assertIn('Error', tools.get_events_from_duke_api_single_input(''))

    @patch('dukebot.tools.requests.get')
    @patch('dukebot.tools.logging.getLogger')
    def test_get_curriculum_with_subject_from_duke_api_success(self, mock_logger, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = '[{"course":1},{"course":2},{"course":3},{"course":4},{"course":5},{"course":6}]'
        result = tools.get_curriculum_with_subject_from_duke_api('AIPI')
        self.assertIn('Courses', result)

    @patch('dukebot.tools.requests.get')
    @patch('dukebot.tools.logging.getLogger')
    def test_get_curriculum_with_subject_from_duke_api_api_error(self, mock_logger, mock_get):
        mock_get.return_value.status_code = 400
        mock_get.return_value.text = 'fail'
        result = tools.get_curriculum_with_subject_from_duke_api('AIPI')
        self.assertIn('Failed to fetch data', result)

    @patch('dukebot.tools.requests.get')
    @patch('dukebot.tools.logging.getLogger')
    def test_get_curriculum_with_subject_from_duke_api_json_error(self, mock_logger, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = 'notjson'
        result = tools.get_curriculum_with_subject_from_duke_api('AIPI')
        self.assertIn('Error: Could not parse API response', result)

    @patch('dukebot.tools.requests.get')
    @patch('dukebot.tools.logging.getLogger')
    def test_get_detailed_course_information_from_duke_api_success(self, mock_logger, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = 'ok'
        result = tools.get_detailed_course_information_from_duke_api('id', '1')
        self.assertIn('ok', result)

    @patch('dukebot.tools.requests.get')
    @patch('dukebot.tools.logging.getLogger')
    def test_get_detailed_course_information_from_duke_api_api_error(self, mock_logger, mock_get):
        mock_get.return_value.status_code = 400
        mock_get.return_value.text = 'fail'
        result = tools.get_detailed_course_information_from_duke_api('id', '1')
        self.assertIn('Failed to fetch data', result)

    def test_get_course_details_single_input_valid(self):
        with patch('dukebot.tools.get_detailed_course_information_from_duke_api', return_value='ok'):
            self.assertIn('ok', tools.get_course_details_single_input('id,1'))

    def test_get_course_details_single_input_invalid(self):
        self.assertIn('Error', tools.get_course_details_single_input('badinput'))

    @patch('dukebot.tools.requests.get')
    @patch('dukebot.tools.logging.getLogger')
    def test_get_people_information_from_duke_api_success(self, mock_logger, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = 'ok'
        result = tools.get_people_information_from_duke_api('name')
        self.assertIn('ok', result)

    @patch('dukebot.tools.requests.get')
    @patch('dukebot.tools.logging.getLogger')
    def test_get_people_information_from_duke_api_api_error(self, mock_logger, mock_get):
        mock_get.return_value.status_code = 400
        mock_get.return_value.text = 'fail'
        result = tools.get_people_information_from_duke_api('name')
        self.assertIn('Failed to fetch data', result)

    @patch('dukebot.tools.filter_candidates', return_value=['A'])
    def test_search_subject_by_code(self, mock_filter):
        with patch('dukebot.tools.valid_subjects', ['A', 'B']):
            self.assertIn('A', tools.search_subject_by_code('A'))

    @patch('dukebot.tools.filter_candidates', return_value=[])
    def test_search_subject_by_code_no_match(self, mock_filter):
        with patch('dukebot.tools.valid_subjects', ['A', 'B']):
            result = tools.search_subject_by_code('Z')
            self.assertEqual(json.loads(result)['matches'], [])

    @patch('dukebot.tools.filter_candidates', return_value=['G'])
    def test_search_group_format(self, mock_filter):
        with patch('dukebot.tools.valid_groups', ['G', 'H']):
            self.assertIn('G', tools.search_group_format('G'))

    @patch('dukebot.tools.filter_candidates', return_value=[])
    def test_search_group_format_no_match(self, mock_filter):
        with patch('dukebot.tools.valid_groups', ['G', 'H']):
            result = tools.search_group_format('Z')
            self.assertEqual(json.loads(result)['matches'], [])

    @patch('dukebot.tools.filter_candidates', return_value=['C'])
    def test_search_category_format(self, mock_filter):
        with patch('dukebot.tools.valid_categories', ['C', 'D']):
            self.assertIn('C', tools.search_category_format('C'))

    @patch('dukebot.tools.filter_candidates', return_value=[])
    def test_search_category_format_no_match(self, mock_filter):
        with patch('dukebot.tools.valid_categories', ['C', 'D']):
            result = tools.search_category_format('Z')
            self.assertEqual(json.loads(result)['matches'], [])

    @patch('dukebot.tools.requests.get')
    def test_get_pratt_info_from_serpapi_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'organic_results': [{'link': 'https://pratt.duke.edu'}]}
        result = tools.get_pratt_info_from_serpapi('query', api_key='key')
        # result is a dict with 'organic_results' key
        links = [item['link'] for item in result['organic_results']]
        self.assertIn('https://pratt.duke.edu', links)

    def test_get_pratt_info_from_serpapi_exception(self):
        with patch('dukebot.tools.requests.get', side_effect=Exception('fail')):
            result = tools.get_pratt_info_from_serpapi('query', api_key='key')
            self.assertIn('Error', result)

    def test_process_serpapi_results_filter_domain(self):
        results = {'organic_results': [{'link': 'https://pratt.duke.edu', 'snippet': 'pratt info'}]}
        filtered = tools.process_serpapi_results(results, filter_domain=True)
        self.assertIn('pratt.duke.edu', str(filtered))

    def test_process_serpapi_results_no_filter(self):
        results = {'organic_results': [{'link': 'https://pratt.duke.edu'}, {'link': 'https://other.com'}]}
        filtered = tools.process_serpapi_results(results, filter_domain=False)
        self.assertIn('pratt.duke.edu', str(filtered))

    def test_process_serpapi_results_empty(self):
        filtered = tools.process_serpapi_results({}, filter_domain=True)
        self.assertEqual(filtered['organic_results'], [])

    @patch('dukebot.tools.requests.get')
    def test_get_curriculum_with_subject_from_duke_api_handles_dict_and_list(self, mock_get):
        from dukebot import tools
        class MockResponse:
            def __init__(self, text, status_code=200):
                self.text = text
                self.status_code = status_code
        # Dict response (realistic Duke API structure)
        dict_response = {
            "ssr_get_courses_resp": {
                "course_search_result": {
                    "subjects": {
                        "subject": {
                            "subject": "AIPI",
                            "subject_lov_descr": "AI for Product Innovation",
                            "course_summaries": {
                                "course_summary": [
                                    {"crse_id": "027568", "crse_offer_nbr": "1", "title_long": "Intro to AI", "descrlong": "Learn AI basics."},
                                    {"crse_id": "027569", "crse_offer_nbr": "1", "title_long": "Advanced AI", "descrlong": "Deep dive into AI."}
                                ]
                            }
                        }
                    }
                }
            }
        }
        # List response (fallback)
        list_response = [
            {"crse_id": "027568", "crse_offer_nbr": "1", "title_long": "Intro to AI", "descrlong": "Learn AI basics."},
            {"crse_id": "027569", "crse_offer_nbr": "1", "title_long": "Advanced AI", "descrlong": "Deep dive into AI."}
        ]
        # Patch requests.get to return dict response
        mock_get.return_value = MockResponse(json.dumps(dict_response))
        summary = tools.get_curriculum_with_subject_from_duke_api("AIPI")
        self.assertIn("AIPI - AI for Product Innovation", summary)
        self.assertIn("Intro to AI", summary)
        # Patch requests.get to return list response
        mock_get.return_value = MockResponse(json.dumps(list_response))
        summary2 = tools.get_curriculum_with_subject_from_duke_api("AIPI")
        self.assertIn("Courses", summary2)
        self.assertIn("Advanced AI", summary2)

if __name__ == '__main__':
    unittest.main() 