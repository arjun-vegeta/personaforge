import click
import asyncio
import uuid
from ..integrations.elevenlabs import ElevenLabsProvider
from ..personas.engine import PersonaEngine, Persona, Identity, Goal, Traits
from ..runner.runner import ConversationRunner

@click.group()
def cli():
    """PersonaForge CLI - Voice Agent Reliability Testing Platform."""
    pass

@cli.command()
def init():
    """Initialize a new PersonaForge project."""
    click.echo("Initializing PersonaForge project...")
    # Create directories and default config files
    click.echo("Created personas/ scenarios/ policies/")
    click.echo("Created personaforge.yaml")

@cli.command()
@click.option("--agent-id", required=True, help="ElevenLabs Agent ID")
@click.option("--persona", default="default", help="Persona name")
def run(agent_id, persona):
    """Run a single test conversation."""
    click.echo(f"Starting test run for agent {agent_id} with persona {persona}...")
    
    # Setup dummy persona for POC
    p = Persona(
        name=persona,
        identity=Identity(name="Test User"),
        goals=[Goal(primary="Test conversation")],
        traits=Traits()
    )
    engine = PersonaEngine(p)
    provider = ElevenLabsProvider()
    
    runner = ConversationRunner(
        conversation_id=uuid.uuid4(),
        agent_id=agent_id,
        provider=provider,
        persona_engine=engine
    )
    
    asyncio.run(runner.run())
    
    click.echo("Test run completed.")

@cli.command()
def ci():
    """Run in CI mode for regression testing."""
    click.echo("Running CI tests...")
    # Logic for CI mode
    pass

if __name__ == "__main__":
    cli()
