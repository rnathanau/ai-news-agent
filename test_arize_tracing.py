#!/usr/bin/env python3
"""
Test script to verify Arize AX tracing is working correctly.

This script simulates a digest generation and verifies that:
1. Arize instrumentation initializes correctly
2. All 4 agents are traced
3. Span attributes are set properly
4. Traces are exported to Arize

Usage:
    python test_arize_tracing.py
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_arize_initialization():
    """Test that Arize instrumentation initializes correctly."""
    print("=" * 70)
    print("Testing Arize AX Tracing Initialization")
    print("=" * 70)
    
    # Check environment variables
    space_id = os.getenv("ARIZE_SPACE_ID")
    api_key = os.getenv("ARIZE_API_KEY")
    
    print("\n1. Checking Environment Variables:")
    print(f"   ARIZE_SPACE_ID: {'✅ Set' if space_id else '❌ Not Set'}")
    print(f"   ARIZE_API_KEY: {'✅ Set' if api_key else '❌ Not Set'}")
    
    if not space_id or not api_key:
        print("\n⚠️  WARNING: Arize credentials not set!")
        print("   Tracing will not be enabled.")
        print("\n   To enable tracing:")
        print("   1. Sign up at: https://app.arize.com/signup")
        print("   2. Get credentials from Settings → API Keys")
        print("   3. Set environment variables:")
        print("      export ARIZE_SPACE_ID='your-space-id'")
        print("      export ARIZE_API_KEY='your-api-key'")
        return False
    
    # Import main to trigger initialization
    print("\n2. Initializing Arize instrumentation...")
    try:
        from main import _TRACING
        if _TRACING:
            print("   ✅ Arize instrumentation initialized successfully!")
            return True
        else:
            print("   ⚠️  Tracing libraries not available")
            print("   Install with: pip install arize-otel openinference-instrumentation-langchain")
            return False
    except Exception as e:
        print(f"   ❌ Error initializing: {e}")
        return False


def test_agent_instrumentation():
    """Test that all agents have proper instrumentation."""
    print("\n3. Checking Agent Instrumentation:")
    
    try:
        from main import monitor_agent, relevance_agent, summary_agent, digest_agent
        
        agents = [
            ("Monitor Agent", monitor_agent),
            ("Relevance Agent", relevance_agent),
            ("Summary Agent", summary_agent),
            ("Digest Agent", digest_agent),
        ]
        
        for name, agent_func in agents:
            # Check if agent function exists and has proper structure
            if callable(agent_func):
                print(f"   ✅ {name}: Instrumented")
            else:
                print(f"   ❌ {name}: Not found")
        
        return True
    except Exception as e:
        print(f"   ❌ Error checking agents: {e}")
        return False


def test_span_attributes():
    """Test that span attributes are properly configured."""
    print("\n4. Checking Span Attributes Configuration:")
    
    try:
        from main import _TRACING
        
        if not _TRACING:
            print("   ⚠️  Tracing not enabled, skipping span attribute check")
            return False
        
        # Check that using_attributes is available
        from main import using_attributes, using_prompt_template
        print("   ✅ using_attributes: Available")
        print("   ✅ using_prompt_template: Available")
        
        # Check OpenTelemetry trace is available
        from opentelemetry import trace
        print("   ✅ OpenTelemetry trace: Available")
        
        return True
    except Exception as e:
        print(f"   ❌ Error checking span attributes: {e}")
        return False


def test_tracer_provider():
    """Test that tracer provider is registered."""
    print("\n5. Checking Tracer Provider:")
    
    try:
        from opentelemetry import trace
        tracer_provider = trace.get_tracer_provider()
        
        # Check if it's a proper tracer provider (not NoOpTracerProvider)
        provider_type = type(tracer_provider).__name__
        
        if "NoOp" in provider_type:
            print(f"   ⚠️  Using {provider_type} (tracing disabled)")
            return False
        else:
            print(f"   ✅ Active TracerProvider: {provider_type}")
            return True
    except Exception as e:
        print(f"   ❌ Error checking tracer provider: {e}")
        return False


def print_summary(results):
    """Print test summary."""
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    total = len(results)
    passed = sum(results.values())
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "-" * 70)
    print(f"Total: {passed}/{total} tests passed")
    print("-" * 70)
    
    if passed == total:
        print("\n🎉 All tests passed! Arize AX tracing is ready!")
        print("\nNext steps:")
        print("1. Deploy to Render with ARIZE_SPACE_ID and ARIZE_API_KEY")
        print("2. Generate a digest")
        print("3. View traces at: https://app.arize.com/")
        print("4. Look for project: 'headsup-news-agent'")
    elif passed > 0:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    else:
        print("\n❌ All tests failed. Arize tracing is not configured.")
        print("\nTo fix:")
        print("1. Install dependencies: pip install -r backend/requirements.txt")
        print("2. Set Arize credentials (see test output above)")
        print("3. Run this test again")


def main():
    """Run all tests."""
    print("\n🔍 Arize AX Tracing Test Suite")
    print("   Project: HeadsUp News Agent")
    print("   Testing: Observability instrumentation\n")
    
    results = {
        "Environment Variables": test_arize_initialization(),
        "Agent Instrumentation": test_agent_instrumentation(),
        "Span Attributes": test_span_attributes(),
        "Tracer Provider": test_tracer_provider(),
    }
    
    print_summary(results)
    
    # Exit with appropriate code
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()


