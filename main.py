import asyncio
import sys
from pathlib import Path

# Add src to python path for direct execution
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import typer
from rich.console import Console
from rich.table import Table

from taobao_crawler_agent import __version__
from taobao_crawler_agent.agent import TaobaoAgent
from taobao_crawler_agent.crawler.browser import BrowserManager
from taobao_crawler_agent.storage.exporter import DataExporter

app = typer.Typer(help="TaobaoCrawlerAgent - Intelligent search, crawler & agent CLI for Taobao")
console = Console()


@app.command()
def version():
    """Show the version of TaobaoCrawlerAgent."""
    console.print(f"[bold cyan]TaobaoCrawlerAgent[/bold cyan] v{__version__}")


@app.command()
def login():
    """Open a visible browser window for you to scan QR code / log in to Taobao to save session."""
    async def _login():
        console.print("[bold yellow]Opening Taobao in interactive mode...[/bold yellow]")
        console.print("[dim]Please complete QR code or SMS login in the opened browser window.[/dim]")
        bm = BrowserManager(headless=False)
        page = await bm.new_page()
        await page.goto("https://login.taobao.com")
        console.print("[green]Waiting for login. Close the browser window or press Enter here when done.[/green]")
        try:
            await page.wait_for_url("https://www.taobao.com/**", timeout=120000)
            console.print("[bold green]Login detected successfully! Session saved.[/bold green]")
        except Exception:
            console.print("[yellow]Timeout or manual close. Session cookies are saved in data/sessions.[/yellow]")
        finally:
            await bm.close()

    asyncio.run(_login())


@app.command()
def search(
    keyword: str = typer.Argument(..., help="Search keyword or product description"),
    headless: bool = typer.Option(True, "--headless/--no-headless", help="Run browser in headless mode"),
    output_format: str = typer.Option("csv", "--format", "-f", help="Export format: csv or json"),
):
    """Run agent to search products on Taobao and summarize results."""
    async def _search():
        console.print(f"[bold blue]Starting agent search for:[/bold blue] '{keyword}'")
        agent = TaobaoAgent(headless=headless)
        result = await agent.run_search(keyword)

        console.print(f"\n[bold green]Search Summary:[/bold green] {result.summary}\n")

        if result.top_recommendations:
            table = Table(title=f"Top Recommendations for '{keyword}'")
            table.add_column("Title", style="cyan", no_wrap=False)
            table.add_column("Price (RMB)", style="green", justify="right")
            table.add_column("Sales", style="magenta")
            table.add_column("Shop", style="yellow")

            for item in result.top_recommendations:
                table.add_row(
                    item.title[:40] + ("..." if len(item.title) > 40 else ""),
                    f"¥{item.price:.2f}",
                    item.sales_count or "-",
                    item.shop_name or "-",
                )
            console.print(table)

            exporter = DataExporter()
            filename = f"search_{keyword.replace(' ', '_')}"
            if output_format.lower() == "json":
                out = exporter.export_json(result.top_recommendations, filename)
            else:
                out = exporter.export_csv(result.top_recommendations, filename)
            console.print(f"[bold]Exported results to:[/bold] [underline]{out}[/underline]")
        else:
            console.print("[yellow]No product items retrieved. If prompted, please run 'python main.py login' first.[/yellow]")

    asyncio.run(_search())


if __name__ == "__main__":
    app()
