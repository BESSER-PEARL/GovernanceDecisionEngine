import argparse
import os

from decision_engine import setup

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Governance Decision Engine',
        description='Agent in charge of enforcing governance policies expressed using the Governance DSL.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-t','--test', action='store_true',
                        help='Start the engine in testing mode (add features and hooks for automatic testing)')
    group.add_argument('-p', '--playground', action='store_true',
                        help='Start the engine in Playground mode')
    parser.add_argument('-P', '--Policy',
                        help='Start the engine with base policy')
    args = parser.parse_args()
    os.environ["ENGINE_TESTING"] = str(args.test)
    os.environ["ENGINE_PLAYGROUND"] = str(args.playground)
    policy_file = str(args.Policy) if args.Policy is not None else None
    if args.playground:
        os.environ["PLAYGROUND_POLICY"] = policy_file
    agent = setup(args.test, args.playground, policy_file)
    agent.run()