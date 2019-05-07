import sys
from leaderboard_generator.test import test


def test_all():
    test.test_two_files()
    test.set_ranks()


if __name__ == '__main__':
    test_case = sys.argv[1]
    if test_case == 'main':
        test.test_main()
    elif test_case == 'test_tie_score_different_bot':
        test.test_tie_score_different_bot()
    else:
        test_all()
